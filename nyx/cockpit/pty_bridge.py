"""PTY bridge para o cockpit (COCKPIT-02).

Spawna subprocess em pseudo-terminal e expõe leitura/escrita assíncrona
para a rota WebSocket `/repl`. Apenas 1 sessão por cockpit (segunda
conexão recebe 'busy').
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
from typing import AsyncIterator

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.cockpit.pty")

DEFAULT_READ_BYTES = 4096


class PtyBridge:
    """Wrapper assíncrono sobre pty.openpty + subprocess.

    Uso:
        bridge = PtyBridge(["./run.sh"])
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

    def start(self) -> None:
        """Cria pty + spawna processo (não-bloqueante)."""
        if self.proc is not None:
            raise RuntimeError("PtyBridge.start() chamado mais de uma vez")
        master_fd, slave_fd = pty.openpty()
        self.master_fd = master_fd
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
