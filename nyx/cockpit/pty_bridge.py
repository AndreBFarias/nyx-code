"""PTY bridge para o cockpit (COCKPIT-02).

Spawna subprocess em pseudo-terminal e expõe leitura/escrita assíncrona
para a rota WebSocket `/repl`. Apenas 1 sessão por cockpit (segunda
conexão recebe 'busy').

COCKPIT-LIFECYCLE-FIX-01 (2026-05-19): integra com NYX_PID_FILE para
detectar instância anterior viva antes de spawnar. Se PID anterior
está vivo, retorna estado 'busy' em vez de causar cascata de kill
no UX-LIFECYCLE-01. Se PID stale (processo morto), limpa lock e
prossegue.
"""

from __future__ import annotations

import asyncio
import fcntl
import os
import pty
import signal
import struct
import subprocess
import termios
from pathlib import Path
from typing import AsyncIterator

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import NYX_PID_FILE

logger = get_logger("nyx.cockpit.pty")

DEFAULT_READ_BYTES = 4096


def _pid_alive(pid: int) -> bool:
    """Espelha Lifecycle._pid_alive para evitar import circular leve."""
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


def inspect_pid_file(path: str | os.PathLike[str] | None = None) -> dict:
    """Inspeciona NYX_PID_FILE antes de spawnar PTY.

    Retorno:
        {"state": "free"}                                 — sem lock
        {"state": "alive", "pid": <N>}                    — instância viva
        {"state": "stale", "pid": <N>, "cleaned": True}   — lock removido
        {"state": "invalid", "cleaned": True}             — conteúdo inválido removido

    Em qualquer estado != 'alive' o caminho fica livre para nova instância.
    """
    target = Path(path if path is not None else NYX_PID_FILE)
    if not target.exists():
        return {"state": "free"}
    try:
        raw = target.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.debug("inspect_pid_file: erro ao ler %s: %s", target, exc)
        return {"state": "free"}
    if not raw:
        try:
            target.unlink()
        except OSError as exc:
            logger.debug("inspect_pid_file: falha ao limpar lock vazio: %s", exc)
        return {"state": "invalid", "cleaned": True}
    try:
        pid = int(raw)
    except ValueError:
        try:
            target.unlink()
        except OSError as exc:
            logger.debug("inspect_pid_file: falha ao limpar lock inválido: %s", exc)
        return {"state": "invalid", "cleaned": True}
    if _pid_alive(pid):
        return {"state": "alive", "pid": pid}
    try:
        target.unlink()
        logger.info("PtyBridge: lock stale (PID=%d morto) removido", pid)
        return {"state": "stale", "pid": pid, "cleaned": True}
    except OSError as exc:
        logger.warning("PtyBridge: falha ao limpar lock stale PID=%d: %s", pid, exc)
        return {"state": "stale", "pid": pid, "cleaned": False}


class PtyBridge:
    """Wrapper assíncrono sobre pty.openpty + subprocess.

    Uso:
        bridge = PtyBridge(["./run.sh"])
        state = bridge.preflight()
        if state["state"] == "alive":
            # sessão já ativa em outro lugar
            return
        bridge.start()
        async for data in bridge.read():
            await ws.send_bytes(data)
    """

    def __init__(self, cmd: list[str], cwd: str | None = None, env: dict | None = None) -> None:
        self.cmd = cmd
        self.cwd = cwd
        self.env = env
        self.proc: subprocess.Popen | None = None
        self.master_fd: int | None = None
        self._closed = False

    def preflight(self) -> dict:
        """COCKPIT-LIFECYCLE-FIX-01: inspeciona NYX_PID_FILE antes de spawn.

        Chamada antes de `start()`. Resultado deve ser checado pelo caller:
        - state='alive' → não spawnar (sessão ativa em outro lugar).
        - state='free'/'stale'/'invalid' → spawn liberado.
        """
        return inspect_pid_file()

    def start(self) -> None:
        """Cria pty + spawna processo (não-bloqueante)."""
        if self.proc is not None:
            raise RuntimeError("PtyBridge.start() chamado mais de uma vez")
        master_fd, slave_fd = pty.openpty()
        self.master_fd = master_fd
        # TUI-FIX-WEB-PTY-INITIAL-WINSIZE-01 (ONDA-34): pty.openpty() nasce 0x0.
        # O Textual iniciava num terminal 0x0 e só re-renderizava quando o resize
        # do xterm.js chegava (pós-onopen) -> render inicial degenerado (input/
        # toolbar ausentes) e empilhamento no resize seguinte. Define 24x80
        # (fallback clássico de TTY) antes do spawn; o resize real do cliente
        # corrige em seguida, mas o 1o frame já sai válido.
        try:
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        except OSError as exc:  # noqa: BLE001 -- best-effort
            logger.debug("winsize inicial falhou: %s", exc)
        # start_new_session=True isola o processo do shell pai
        # (evita herdar TTY do cockpit server)
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            start_new_session=True,
            cwd=self.cwd,
            env=self.env,
            close_fds=True,
        )
        os.close(slave_fd)
        logger.info(
            "PTY spawnado: cmd=%s pid=%s master_fd=%s",
            self.cmd, self.proc.pid, self.master_fd,
        )

    def resize(self, rows: int, cols: int) -> None:
        """Redimensiona o PTY (informa o subprocess via TIOCSWINSZ)."""
        if self.master_fd is None:
            return
        # struct: rows, cols, xpix, ypix
        try:
            packed = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, packed)
        except OSError as exc:  # noqa: BLE001 -- resize best-effort
            logger.debug("Falha ao redimensionar PTY %sx%s: %s", rows, cols, exc)

    async def read(self) -> AsyncIterator[bytes]:
        """Stream assíncrono do master_fd. Encerra quando o processo morre."""
        if self.master_fd is None:
            return
        loop = asyncio.get_running_loop()
        while not self._closed:
            try:
                data = await loop.run_in_executor(
                    None, os.read, self.master_fd, DEFAULT_READ_BYTES
                )
            except OSError as exc:
                logger.debug("PTY read encerrou: %s", exc)
                return
            if not data:
                return
            yield data

    def write(self, data: bytes) -> None:
        """Escreve no master_fd (do browser para o processo)."""
        if self.master_fd is None or self._closed:
            return
        try:
            os.write(self.master_fd, data)
        except OSError as exc:  # noqa: BLE001 -- write best-effort
            logger.debug("PTY write falhou: %s", exc)

    def close(self) -> None:
        """Encerra processo + libera master_fd. Idempotente."""
        if self._closed:
            return
        self._closed = True
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.send_signal(signal.SIGTERM)
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                logger.warning("PTY SIGTERM timeout; enviando SIGKILL pid=%s", self.proc.pid)
                self.proc.kill()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    logger.error("PTY pid=%s ignorou SIGKILL", self.proc.pid)
            except Exception as exc:  # noqa: BLE001 -- shutdown best-effort
                logger.warning("Falha ao encerrar processo PTY: %s", exc)
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except OSError as exc:
                logger.debug("Falha ao fechar master_fd (já fechado?): %s", exc)
            self.master_fd = None
        logger.info("PtyBridge encerrada")
