"""Lifecycle -- single-instance via PID file, OOM check pré-inferência.

Responsabilidades (UX-LIFECYCLE-01):

1. `acquire`: garante única instância viva por PID file. Stale lock
   (PID não vive mais) é silenciosamente sobrescrito. Lock vivo é
   morto via SIGTERM (5s timeout) e fallback SIGKILL.

2. `release`: invoca callbacks registrados (cleanup de Ollama/proxy)
   e remove o PID file. Registrado em `atexit` automaticamente após
   `acquire` bem-sucedido.

3. `vram_check`: lê `nvidia-smi` com timeout curto. Graceful em falha
   (assume OK se ferramenta ausente ou retorno inesperado).

Não substitui `kill_existing_ollama` do `run.sh` (que cuida da porta
Ollama por outro caminho); complementa-o no nível do processo `run.sh`
master.
"""

from __future__ import annotations

import atexit
import os
import signal
import subprocess
import time
from pathlib import Path

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import NYX_PID_FILE

logger = get_logger("nyx.lifecycle")

# Timeout (segundos) que SIGTERM tem para encerrar instância anterior
# antes de cair para SIGKILL. 5s cobre proxy + Ollama em desligamento gracioso.
_SIGTERM_WAIT_S: float = 5.0
_SIGTERM_POLL_S: float = 0.1

# Limite default de VRAM livre (MiB) para liberar inferência cold.
# 800 MiB cobre o footprint mínimo do qwen2.5-coder:3b mesmo com num_gpu baixo.
DEFAULT_VRAM_THRESHOLD_MIB: int = 800


class Lifecycle:
    """Gerenciador de PID file + checks de recurso."""

    def __init__(self, pid_file: str | os.PathLike[str] | None = None) -> None:
        target = pid_file if pid_file is not None else NYX_PID_FILE
        self._pidfile = Path(target)
        self._cleanup_callbacks: list = []
        self._acquired: bool = False

    @property
    def pidfile(self) -> Path:
        return self._pidfile

    def acquire(self) -> bool:
        """Lock file. Mata anterior gracefully se PID vivo. Retorna True sempre.

        COCKPIT-LIFECYCLE-FIX-01: respeita env `NYX_LIFECYCLE_TAKEOVER`.
        - takeover=1 (default): comportamento legado, mata anterior.
        - takeover=0: aborta se anterior vivo (retorna False sem mexer no PID file).
        Cockpit usa takeover=0 para não causar cascata de kill no proxy.
        """
        takeover = os.environ.get("NYX_LIFECYCLE_TAKEOVER", "1").strip()
        self._pidfile.parent.mkdir(parents=True, exist_ok=True)
        if self._pidfile.exists():
            old_pid = self._read_pid()
            if old_pid and self._pid_alive(old_pid):
                if takeover == "0":
                    logger.info(
                        "instância anterior PID=%d viva e NYX_LIFECYCLE_TAKEOVER=0; abortando",
                        old_pid,
                    )
                    return False
                logger.info("matando instância anterior PID=%d", old_pid)
                self._terminate_gracefully(old_pid)
            elif old_pid:
                logger.info("lock stale (PID=%d morto), sobrescrevendo", old_pid)
        try:
            self._pidfile.write_text(str(os.getpid()))
        except OSError as exc:
            logger.warning("falha ao gravar PID file %s: %s", self._pidfile, exc)
            return False
        atexit.register(self.release)
        self._acquired = True
        return True

    def release(self) -> None:
        """Roda callbacks registrados e remove o PID file. Idempotente."""
        if not self._acquired:
            return
        for cb in list(self._cleanup_callbacks):
            try:
                cb()
            except Exception as exc:  # noqa: BLE001 -- callback do app, não derrubar release
                logger.warning("cleanup callback raised: %s", exc)
        if self._pidfile.exists():
            try:
                content = self._read_pid()
                # Só remove se o PID dentro é o nosso (não roubar lock de outro).
                if content == os.getpid() or content == 0:
                    self._pidfile.unlink()
            except OSError as exc:
                logger.warning("falha ao remover PID file %s: %s", self._pidfile, exc)
        self._acquired = False

    def register_cleanup(self, fn) -> None:
        """Adiciona callback invocado em `release` (ordem de inserção)."""
        self._cleanup_callbacks.append(fn)

    def vram_check(self, threshold_mib: int = DEFAULT_VRAM_THRESHOLD_MIB) -> tuple[bool, int]:
        """Lê VRAM livre via nvidia-smi. Retorna (ok, livre_mib).

        - `ok=True, livre=N`: VRAM suficiente.
        - `ok=False, livre=N`: VRAM insuficiente (N < threshold).
        - `ok=True, livre=-1`: nvidia-smi indisponível; assume OK (degrada para fluxo normal).
        """
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.debug("vram_check: nvidia-smi indisponível (%s)", type(exc).__name__)
            return (True, -1)
        except OSError as exc:
            logger.debug("vram_check: erro de OS (%s)", exc)
            return (True, -1)
        raw = (result.stdout or "").strip().splitlines()
        if not raw:
            return (True, -1)
        try:
            free = int(raw[0].strip())
        except ValueError:
            logger.debug("vram_check: saída inválida: %r", raw[0])
            return (True, -1)
        return (free >= threshold_mib, free)

    def _read_pid(self) -> int:
        try:
            raw = self._pidfile.read_text().strip()
        except OSError:
            return 0
        if not raw:
            return 0
        try:
            return int(raw)
        except ValueError:
            return 0

    def _terminate_gracefully(self, pid: int) -> None:
        """SIGTERM com timeout; SIGKILL fallback. Tolerante a race."""
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except PermissionError as exc:
            logger.warning("sem permissão para SIGTERM PID=%d: %s", pid, exc)
            return
        deadline = time.monotonic() + _SIGTERM_WAIT_S
        while time.monotonic() < deadline:
            if not self._pid_alive(pid):
                return
            time.sleep(_SIGTERM_POLL_S)
        if self._pid_alive(pid):
            logger.warning("PID=%d sobreviveu SIGTERM, enviando SIGKILL", pid)
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError) as exc:
                logger.debug("SIGKILL race para PID=%d: %s", pid, exc)

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # Processo existe mas pertence a outro UID. Assume vivo.
            return True
        except OSError:
            return False
        return True


# "Cada processo deixado para trás é um custo cobrado da próxima vez." -- princípio anti-débito
