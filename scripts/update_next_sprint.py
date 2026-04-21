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
    r"^\|\s*\d+\s*\|\s*\*\*([A-Z][A-Z0-9_\-]+)\*\*\s*\|.*\|\s*PENDENTE\s*\|",
    re.MULTILINE,
)

# Tolera blockquote ('> ') opcional, asteriscos em torno de 'Status' (com
# colon dentro OU fora dos asteriscos: `**Status:**` e `**Status**:`).
# Captura o primeiro campo Status explícito do arquivo da sprint.
_STATUS_RE = re.compile(
    r"^(?:>\s*)?\*{0,2}Status:?\*{0,2}:?\s*([A-Z][A-Z0-9_\-]*)",
    re.MULTILINE,
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
    """Lê o primeiro campo 'Status' do arquivo da sprint.

    Tolera blockquote (``> **Status:** ...``) e variações em asteriscos.
    Retorna ``"DESCONHECIDO"`` quando o arquivo não tem campo Status legível.
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:8000]
    except OSError as exc:
        logger.warning("não foi possível ler %s: %s", path, exc)
        return "DESCONHECIDO"
    match = _STATUS_RE.search(head)
    return match.group(1) if match else "DESCONHECIDO"


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


def find_next_pending() -> str | None:
    """Retorna o ID da primeira sprint PENDENTE válida.

    Itera sobre as linhas PENDENTE do SPRINT_ORDER_MASTER.md (fonte de ordem
    canônica) e descarta aquelas cujo arquivo físico em ``producao/`` tem
    Status fora da whitelist. Garante que fantasmas (ABSORVIDA/DEFERIDA/
    CONCLUIDA que ainda sobrevivem em producao/) não sejam eleitos.
    """
    if not MASTER.exists():
        logger.error("%s não encontrado", MASTER)
        return None
    content = MASTER.read_text(encoding="utf-8")
    for match in ROW_PATTERN.finditer(content):
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
Protocolo obrigatório (CLAUDE.md seção "próxima sprint" + workflow anti-gambiarra):

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
10. Após CONCLUIDA: commit atômico, move sprint file para concluidos/, roda `python scripts/update_next_sprint.py` para atualizar este arquivo.

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
