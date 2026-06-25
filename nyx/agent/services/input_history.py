"""InputHistory -- histórico persistente das mensagens enviadas no input da TUI.

INPUT-HISTORY-RECALL-01 (ONDA-47): paridade de ergonomia com shells/REPLs --
Up no input vazio (ou com o cursor na primeira linha) traz a mensagem anterior,
Up de novo recua para as mais antigas, Down avança de volta para as mais
recentes e ao rascunho. O recall em si vive na TUI (`nyx/agent/tui/app.py`);
este service guarda o lado persistente: carrega o histórico no boot e faz append
do texto enviado em `~/.nyx/input_history` (uma entrada por linha, cap de 500).

Formato do arquivo: uma submissão por linha. Como as mensagens podem ser
multilinha, a quebra interna (`\\n`) é escapada como `\\n` literal no disco e
desescapada na leitura -- assim cada linha física do arquivo corresponde a
exatamente uma submissão lógica, e o cap por contagem de linhas é fiel.

Service importável de `nyx/agent/services/` (ADR-013): o arquivo existe no
diretório de services e importa sem efeito colateral pesado (o I/O só acontece
quando a TUI instancia `InputHistory`).
"""

from __future__ import annotations

from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.services.input_history")

HISTORY_FILE = Path.home() / ".nyx" / "input_history"

# Cap de entradas mantidas em disco e em memória. ~500 cobre semanas de uso sem
# inflar o arquivo (decisão do spec: "cap razoável, ex.: ultimas 500").
MAX_ENTRIES = 500


def _encode(text: str) -> str:
    """Serializa uma submissão para uma única linha física.

    Escapa a barra invertida primeiro (para não colidir com o escape de quebra)
    e depois o `\\n`. Resultado nunca contém quebra de linha real.
    """
    return text.replace("\\", "\\\\").replace("\n", "\\n")


def _decode(line: str) -> str:
    """Inverso de `_encode`: restaura `\\n` e a barra invertida literal.

    Faz o parse caractere a caractere para distinguir `\\n` (quebra escapada) de
    `\\\\n` (barra invertida literal seguida de 'n'), evitando o bug de um
    `replace` ingênuo que trocaria os dois indistintamente.
    """
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == "\\" and i + 1 < n:
            nxt = line[i + 1]
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


class InputHistory:
    """Histórico de submissões do input, carregado no boot e persistido a cada envio.

    Uso na TUI:
        hist = InputHistory()          # carrega ~/.nyx/input_history
        entries = hist.entries         # lista cronológica (antigo -> recente)
        hist.append("minha mensagem")  # dedup do consecutivo + cap + persiste

    `entries` é uma cópia defensiva: o caller (a TUI) mantém o próprio cursor de
    navegação sobre a lista que recebe; mutações nela não afetam o disco.
    """

    def __init__(self, path: Path | None = None, max_entries: int = MAX_ENTRIES) -> None:
        self._path = path if path is not None else HISTORY_FILE
        self._max = max_entries
        self._entries: list[str] = []
        self._load()

    def _load(self) -> None:
        """Lê o arquivo de histórico (best-effort: ausência/erro = lista vazia)."""
        if not self._path.exists():
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Falha ao ler histórico de input %s: %s", self._path, exc)
            return
        self._entries = [
            _decode(line) for line in raw.splitlines() if line != ""
        ]
        # Respeita o cap mesmo que o arquivo em disco tenha crescido além dele.
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max :]

    @property
    def entries(self) -> list[str]:
        """Cópia cronológica (mais antigo primeiro) das submissões guardadas."""
        return list(self._entries)

    def append(self, text: str) -> None:
        """Acrescenta uma submissão, aplica dedup do consecutivo, cap e persiste.

        Texto vazio/só-espaços é ignorado (não há mensagem real para lembrar).
        Dedup só do consecutivo (não global): Enter repetido do mesmo comando
        não polui o histórico, mas reusos espaçados preservam a ordem de uso --
        mesma semântica do `_input_history` da TUI.
        """
        if not text.strip():
            return
        if self._entries and self._entries[-1] == text:
            return
        self._entries.append(text)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max :]
        self._persist()

    def _persist(self) -> None:
        """Escreve o histórico inteiro (já capado) no arquivo, uma entrada por linha."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = "\n".join(_encode(e) for e in self._entries)
            if payload:
                payload += "\n"
            self._path.write_text(payload, encoding="utf-8")
        except OSError as exc:
            logger.warning("Falha ao gravar histórico de input %s: %s", self._path, exc)

    def __len__(self) -> int:
        return len(self._entries)


__all__ = ["InputHistory", "HISTORY_FILE", "MAX_ENTRIES"]


# "Quem não lembra o que digitou, redigita." -- anônimo
