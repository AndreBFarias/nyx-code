#!/usr/bin/env python3
"""Atualiza EXECUTAR_SPRINT.md com a próxima sprint PENDENTE.

Lê dev-journey/06-sprints/SPRINT_ORDER_MASTER.md, encontra a primeira
sprint marcada como PENDENTE na tabela da Onda em execução, e injeta
o ID no template EXECUTAR_SPRINT.md na raiz.

Uso:
    python scripts/update_next_sprint.py
    python scripts/update_next_sprint.py --show     # só imprime, não grava

Roda automaticamente (sugestão): após marcar sprint como CONCLUIDA e commitar.
Pode ser wired como post-commit hook se o usuário quiser.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MASTER = PROJECT_ROOT / "dev-journey" / "06-sprints" / "SPRINT_ORDER_MASTER.md"
TARGET = PROJECT_ROOT / "EXECUTAR_SPRINT.md"
PRODUCAO_DIR = PROJECT_ROOT / "dev-journey" / "06-sprints" / "producao"
GAMBIARRAS_PATH = (
    PROJECT_ROOT / "dev-journey" / "08-templates" / "GAMBIARRAS_POR_SPRINT.md"
)

INJECT_BEGIN = "<!-- GAMBIARRAS_INJECT -->"
INJECT_END = "<!-- /GAMBIARRAS_INJECT -->"
MAX_INJECT_LINES = 50

ROW_PATTERN = re.compile(
    r"^\|\s*[A-Z]?\d+\s*\|\s*\*\*([A-Z][A-Z0-9_\-]+)\*\*\s*\|.*\|\s*PENDENTE\s*\|",
    re.MULTILINE,
)

# SPRINT_ORDER-OVERRIDE-FIX-01: blocos MANUAL_OVERRIDE_ONDA_NN_START..END canonizam
# a ordem de sprints da Onda NN. Prioridade DESC: Onda mais recente vence quando
# múltiplos blocos têm sprints PENDENTE.
_OVERRIDE_BLOCK_RE = re.compile(
    r"<!--\s*MANUAL_OVERRIDE_ONDA_(\d+)_START\s*-->(.*?)<!--\s*MANUAL_OVERRIDE_ONDA_\d+_END\s*-->",
    re.DOTALL,
)

# Tolera blockquote ('> ') opcional, asteriscos em torno de 'Status' (com
# colon dentro OU fora dos asteriscos: `**Status:**` e `**Status**:`).
# Captura o primeiro campo Status explícito do arquivo da sprint.
_STATUS_RE = re.compile(
    r"^(?:>\s*)?\*{0,2}Status:?\*{0,2}:?\s*([A-Z][A-Z0-9_\-]*)",
    re.MULTILINE,
)

# Blocos de código (cerca tripla) — removidos antes da busca de Status para
# ignorar '**Status:** ...' que esteja citado dentro de bloco Python/YAML/md.
_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

# Seções de ADR embedded no corpo da sprint (ex: SPRINT_VISION_01.md cita
# ADR-022 inline). Remover a região 'ADR-xxx ... próximo heading de mesmo
# nível não-ADR' antes da busca evita que '**Status:** ACEITO' do ADR
# citado seja confundido com o Status da sprint.
_ADR_SECTION_RE = re.compile(
    r"^#\s+ADR[-_ ].*?(?=^#\s+(?!ADR[-_ ])|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)

# Whitelist: só consideramos sprints com este status literal no arquivo físico.
_VALID_STATUS = {"PENDENTE"}

logger = logging.getLogger("update_next_sprint")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def _read_status(path: Path) -> str:
    """Lê o campo 'Status' da região canônica de metadata da sprint.

    Antes de buscar ``**Status:**``, mascara dois tipos de região onde o
    campo pode aparecer de forma "alienígena":

      - Blocos de código (````` ... `````) — Status em snippet de exemplo.
      - Seções de ADR embedded (``# ADR-022 ...`` até próximo heading de
        mesmo nível que não seja outro ADR) — o ADR citado tem Status
        próprio (ex: ``ACEITO``) que não é da sprint.

    A metadata da sprint é tipicamente ``**Status:** PENDENTE`` em linha
    solta, em um dos dois padrões canônicos de ``SPRINT_TEMPLATE_V2.md``:
    antes do heading ``# Sprint <ID>`` (padrão novo), ou depois dele
    (padrão CTX-04). Ambos sobrevivem ao mascaramento.

    Retornos:
      - Status canônico (ex: ``"PENDENTE"``) quando o campo foi encontrado.
      - ``"SEM_METADATA"`` quando o arquivo não tem Status legível
        (template violado) — emite warning com hint acionável.
      - ``"DESCONHECIDO"`` apenas em erro de I/O.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:8000]
    except OSError as exc:
        logger.warning("não foi possível ler %s: %s", path, exc)
        return "DESCONHECIDO"

    masked = _CODE_FENCE_RE.sub("", text)
    masked = _ADR_SECTION_RE.sub("", masked)

    match = _STATUS_RE.search(masked)
    if match:
        return match.group(1)

    logger.warning(
        "sprint %s sem campo Status na região de metadata -- "
        "adicione '**Status:** PENDENTE' em linha própria após o bloco YAML "
        "(0. SPEC), conforme SPRINT_TEMPLATE_V2.md",
        path.name,
    )
    return "SEM_METADATA"


def _scan_producao_statuses() -> dict[str, str]:
    """Varre producao/*.md e emite log 'pulando' para status não-PENDENTE.

    Retorna mapa ``{nome_arquivo: status}`` para uso posterior pelo seletor.
    Efeito colateral: logs diagnósticos de cada sprint não-PENDENTE.
    """
    statuses: dict[str, str] = {}
    if not PRODUCAO_DIR.is_dir():
        return statuses
    for p in sorted(PRODUCAO_DIR.glob("SPRINT_*.md")):
        status = _read_status(p)
        statuses[p.name] = status
        if status not in _VALID_STATUS:
            logger.info("pulando %s (status=%s)", p.name, status)
    return statuses


def _scan_block_for_pending(block: str) -> str | None:
    """Procura primeira sprint PENDENTE válida dentro de um trecho do MASTER.

    Reutiliza ROW_PATTERN + _read_status do arquivo físico em producao/.
    SPRINT_ORDER-OVERRIDE-FIX-01: helper extraído para suportar blocos
    MANUAL_OVERRIDE_ONDA_NN antes do fallback legado.
    """
    for match in ROW_PATTERN.finditer(block):
        sprint_id = match.group(1)
        sprint_path = PRODUCAO_DIR / sprint_file_name(sprint_id)
        if not sprint_path.exists():
            logger.info(
                "pulando %s (arquivo ausente em producao/)", sprint_path.name
            )
            continue
        status = _read_status(sprint_path)
        if status in _VALID_STATUS:
            return sprint_id
        logger.info("pulando %s (status=%s)", sprint_path.name, status)
    return None


def find_next_pending() -> str | None:
    """Retorna o ID da primeira sprint PENDENTE válida.

    SPRINT_ORDER-OVERRIDE-FIX-01: prioriza blocos MANUAL_OVERRIDE_ONDA_NN do
    MASTER (ordem DESC por número da Onda). Cai para regex global apenas se
    nenhum override tiver PENDENTE elegível. Garante que sprints da Onda
    ativa (ex: 26) vençam sprints legadas pré-onda (ex: INFRA-MODEL-AGNOSTIC).

    Itera sobre as linhas PENDENTE e descarta aquelas cujo arquivo físico em
    ``producao/`` tem Status fora da whitelist. Garante que fantasmas
    (ABSORVIDA/DEFERIDA/CONCLUIDA que ainda sobrevivem em producao/) não
    sejam eleitos.
    """
    if not MASTER.exists():
        logger.error("%s não encontrado", MASTER)
        return None
    content = MASTER.read_text(encoding="utf-8")
    # Prioridade 1: blocos MANUAL_OVERRIDE ordenados DESC pelo número da Onda.
    blocks: list[tuple[int, str]] = [
        (int(m.group(1)), m.group(2))
        for m in _OVERRIDE_BLOCK_RE.finditer(content)
    ]
    blocks.sort(key=lambda b: b[0], reverse=True)
    for onda_num, block_content in blocks:
        result = _scan_block_for_pending(block_content)
        if result is not None:
            logger.info("escolha via MANUAL_OVERRIDE_ONDA_%d", onda_num)
            return result
    # Prioridade 2 (fallback legado): regex global sobre o MASTER inteiro.
    return _scan_block_for_pending(content)


def sprint_file_name(sprint_id: str) -> str:
    return "SPRINT_" + sprint_id.replace("-", "_") + ".md"


def _extract_gambiarras_section(
    sprint_id: str, gambiarras_path: Path = GAMBIARRAS_PATH
) -> str:
    """Extrai a seção específica de um sprint ID do catálogo GAMBIARRAS_POR_SPRINT.md.

    Busca marcador ``### {sprint_id}`` no documento e retorna conteúdo até a
    próxima seção ``###`` ou ``##``. Se não achar, devolve mensagem curta com
    aponte para ler o catálogo inteiro.
    """
    if not gambiarras_path.exists():
        return f"(catálogo {gambiarras_path.name} não encontrado)"

    content = gambiarras_path.read_text(encoding="utf-8")
    marker = f"### {sprint_id}"
    idx = content.find(marker)
    if idx == -1:
        return (
            f"(seção específica para {sprint_id} não encontrada em "
            f"{gambiarras_path.name}; ler catálogo universal e matriz geral)"
        )

    rest = content[idx:]
    next_section_idx = len(marker)
    next_markers = ("\n### ", "\n## ", "\n---\n")
    cut = len(rest)
    for m in next_markers:
        found = rest.find(m, next_section_idx)
        if found != -1 and found < cut:
            cut = found
    snippet = rest[:cut].rstrip()

    lines = snippet.splitlines()
    if len(lines) > MAX_INJECT_LINES:
        lines = lines[:MAX_INJECT_LINES]
        lines.append(
            f"(...) ver {gambiarras_path.name} seção {sprint_id} para conteúdo completo"
        )
    return "\n".join(lines)


def count_pending() -> int:
    if not MASTER.exists():
        return 0
    content = MASTER.read_text(encoding="utf-8")
    return len(ROW_PATTERN.findall(content))


def build_prompt(sprint_id: str, remaining: int) -> str:
    fname = sprint_file_name(sprint_id)
    sprint_path = PRODUCAO_DIR / fname
    sprint_exists_note = (
        ""
        if sprint_path.exists()
        else f"\n> AVISO: {sprint_path} não existe. Verifique SPRINT_ORDER_MASTER.md.\n"
    )
    gambiarras_snippet = _extract_gambiarras_section(sprint_id)
    gambiarras_block = (
        f"{INJECT_BEGIN}\n\n"
        f"## Gambiarras específicas (recorte auto-injetado)\n\n"
        f"> Fonte canônica: `dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` "
        f"§{sprint_id}. O bloco abaixo é renovado a cada `python scripts/update_next_sprint.py`.\n\n"
        f"{gambiarras_snippet}\n\n"
        f"{INJECT_END}"
    )
    return f"""# Executar próxima sprint — {sprint_id}

> **Este arquivo é auto-atualizado por `scripts/update_next_sprint.py` após cada sprint concluída.**
> Copie o bloco abaixo e cole em uma session nova de Claude Opus 4.7.
> Restam **{remaining}** sprints PENDENTE(S) na fila.{sprint_exists_note}

---

## Prompt para colar na session

```
Execute /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/producao/{fname}.

Modelo obrigatório: claude-opus-4-7 (sem subagentes).
Protocolo obrigatório (GUIDE.md seção "próxima sprint" + workflow anti-gambiarra):

1. Leia o arquivo da sprint inteiro.
2. Leia a seção correspondente em dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md.
3. Rode `bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1` e me mostre FAIL_BEFORE.
4. Apresente plano e me pergunte dúvidas ANTES de mexer em código.
5. Implemente seguindo literalmente o arquivo da sprint.
6. Rode `bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1` e me mostre FAIL_AFTER.
7. Cole o diff de /tmp/inv_before.txt /tmp/inv_after.txt.
8. Cole o output bruto dos comandos de verificação da sprint.
9. Só marque CONCLUIDA se TODOS os critérios binários + invariantes passarem.
   Regra binária: FAIL_AFTER <= FAIL_BEFORE. Caso contrário, regressão: `git reset --hard HEAD~1` e refazer.
10. Após CONCLUIDA: commit atômico, move sprint file para concluidos/, roda
    `python scripts/update_next_sprint.py` para atualizar este arquivo.

Se qualquer passo falhar, reporte:
    [SPRINT {sprint_id}] BLOQUEADA: <motivo objetivo>

ID desta sprint: {sprint_id}
Arquivo: dev-journey/06-sprints/producao/{fname}
```

---

{gambiarras_block}

---

## Após concluída esta sprint

```bash
# Marcar no master como CONCLUIDA, mover arquivo, re-rodar este script
python scripts/update_next_sprint.py
git add EXECUTAR_SPRINT.md dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
# incluir no mesmo commit da sprint ou em commit separado
```

O arquivo acima será atualizado com o próximo ID automaticamente.
"""


def _write_if_changed(path: Path, new_content: str) -> bool:
    """Escreve apenas se o conteúdo mudou. Retorna True se mudou."""
    if path.exists() and path.read_text(encoding="utf-8") == new_content:
        return False
    path.write_text(new_content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="imprime prompt completo sem gravar")
    parser.add_argument("--quiet", action="store_true", help="não imprime nada (só escreve se mudou)")
    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.WARNING)

    try:
        _scan_producao_statuses()
        sprint_id = find_next_pending()
        remaining = count_pending()
    except Exception as e:
        if not args.quiet:
            print(f"[erro] {e}", file=sys.stderr)
        return 1

    if sprint_id is None:
        content = (
            "# Nenhuma sprint PENDENTE\n\n"
            "> Todas as sprints da Onda atual em `SPRINT_ORDER_MASTER.md` estão concluídas "
            "ou em outro status.\n> Verifique se há nova onda a iniciar ou sprints a reabrir.\n\n"
            "Rodar: `bash scripts/sprint_invariants.sh` para checar se repo está limpo.\n"
        )
        if args.show:
            print(content)
            return 0
        changed = _write_if_changed(TARGET, content)
        if not args.quiet:
            suffix = " [atualizado]" if changed else ""
            print(f"nenhuma sprint PENDENTE{suffix}")
        return 0

    prompt = build_prompt(sprint_id, remaining)

    if args.show:
        print(prompt)
        return 0

    changed = _write_if_changed(TARGET, prompt)
    if not args.quiet:
        suffix = " [atualizado]" if changed else ""
        print(f"próxima sprint: {sprint_id} ({remaining} pendentes){suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# "Automatizar o ritual é livrá-lo da esquecimento." -- anônimo
