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
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MASTER = PROJECT_ROOT / "dev-journey" / "06-sprints" / "SPRINT_ORDER_MASTER.md"
TARGET = PROJECT_ROOT / "EXECUTAR_SPRINT.md"
PRODUCAO_DIR = PROJECT_ROOT / "dev-journey" / "06-sprints" / "producao"

ROW_PATTERN = re.compile(
    r"^\|\s*\d+\s*\|\s*\*\*([A-Z][A-Z0-9_\-]+)\*\*\s*\|.*\|\s*PENDENTE\s*\|",
    re.MULTILINE,
)


def find_next_pending() -> str | None:
    """Retorna o ID da primeira sprint PENDENTE encontrada em ordem."""
    if not MASTER.exists():
        print(f"[erro] {MASTER} não encontrado", file=sys.stderr)
        return None
    content = MASTER.read_text(encoding="utf-8")
    match = ROW_PATTERN.search(content)
    if not match:
        return None
    sprint_id = match.group(1)
    # Normalizar: AUDIT-FIX-02 -> AUDIT_FIX_02 para match com nome de arquivo
    return sprint_id


def sprint_file_name(sprint_id: str) -> str:
    return "SPRINT_" + sprint_id.replace("-", "_") + ".md"


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

## Após concluída esta sprint

```bash
# Marcar no master como CONCLUIDA, mover arquivo, re-rodar este script
python scripts/update_next_sprint.py
git add EXECUTAR_SPRINT.md dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
# incluir no mesmo commit da sprint ou em commit separado
```

O arquivo acima será atualizado com o próximo ID automaticamente.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--show", action="store_true", help="imprime sem gravar")
    args = parser.parse_args()

    sprint_id = find_next_pending()
    remaining = count_pending()

    if sprint_id is None:
        content = f"""# Nenhuma sprint PENDENTE

> Todas as sprints da Onda atual em `SPRINT_ORDER_MASTER.md` estão concluídas ou em outro status.
> Verifique se há nova onda a iniciar ou sprints a reabrir.

Rodar: `bash scripts/sprint_invariants.sh` para checar se repo está limpo.
"""
        if args.show:
            print(content)
            return 0
        TARGET.write_text(content, encoding="utf-8")
        print(f"[ok] nenhuma sprint PENDENTE — {TARGET} atualizado")
        return 0

    prompt = build_prompt(sprint_id, remaining)

    if args.show:
        print(prompt)
        return 0

    TARGET.write_text(prompt, encoding="utf-8")
    print(f"[ok] próxima sprint: {sprint_id} ({remaining} pendentes)")
    print(f"[ok] arquivo atualizado: {TARGET.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# "Automatizar o ritual é livrá-lo da esquecimento." -- anônimo
