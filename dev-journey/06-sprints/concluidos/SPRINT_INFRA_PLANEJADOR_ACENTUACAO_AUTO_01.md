## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-PLANEJADOR-ACENTUACAO-AUTO-01
  title: "Planejador-sprint emite specs com acentuação PT-BR correta + sanitizer local opcional"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Infra
  dependencias: [INFRA-OOM-HISTORY-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/.claude/agents/planejador-sprint.md
      reason: "Adicionar regra explícita PT-BR acentuado no template do agente global (acentos completos em todas as palavras técnicas em português, exceto identificadores literais com noqa-acento)"
      linhas_alvo: "EOF (adicionar bloco de invariante PT-BR)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sanitize_spec_acentuacao.py
      reason: "Script local opcional: roda validar-acentuacao.py --paths no spec recém-gerado + sugere correções automáticas via regex de substituição de 20 palavras-padrão"
      linhas_alvo: "ARQUIVO NOVO"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sanitize_spec_acentuacao.py
      reason: "Helper que aplica regex de fix de acentuação a specs recém-gerados"

  removes: []

  forbidden:
    - "Remover qualquer regra existente do planejador-sprint global"
    - "Quebrar fluxo de /sprint-ciclo em outros projetos"
    - "Adicionar emoji ou menção a IA externa"
    - "Tocar nyx/, dev-journey/, ou outros arquivos do projeto Nyx"

  tests:
    - cmd: "python3 -c 'from pathlib import Path; p = Path.home() / \".claude/agents/planejador-sprint.md\"; t = p.read_text(); assert \"acentuação PT-BR\" in t or \"PT-BR acentuado\" in t, \"regra ausente\"; print(\"OK\")'"
      timeout: 5
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14 FAIL=0"
    - cmd: "python3 scripts/sanitize_spec_acentuacao.py --help"
      timeout: 5
      deve_passar: true
      assert: "imprime ajuda sem crash"

  acceptance_criteria:
    - "Template do planejador-sprint global contém invariante explícita PT-BR acentuado"
    - "Script scripts/sanitize_spec_acentuacao.py existe e executa --help sem crash"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0 nos arquivos novos"
    - "Sprint movida producao/ → concluidos/; MASTER 125jj PENDENTE → CONCLUIDA"
```

---

# Sprint INFRA-PLANEJADOR-ACENTUACAO-AUTO-01

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Problema

Specs gerados pelo `planejador-sprint` global têm 43+ violações sistemáticas de acentuação PT-BR (`nao`, `sessao`, `execucao`, etc.). Executor-sprint herda e propaga. Cada sprint precisa fix-inline = retrabalho.

## Solução

Defesa em 2 camadas:
1. **Preventiva (template do agente global):** adicionar invariante PT-BR explícita no `~/.claude/agents/planejador-sprint.md` para que specs novos já nasçam com acentos.
2. **Corretiva (script local opcional):** `scripts/sanitize_spec_acentuacao.py` que roda no spec recém-gerado e sugere correções via regex.

## Arquivos alvo

### `~/.claude/agents/planejador-sprint.md`

Adicionar ao fim:
```markdown

## Invariante PT-BR

Toda saída user-facing (specs, descrições, comentários, mensagens de commit sugeridas) DEVE usar acentos PT-BR completos:

- ã, ç, é, ó, ú, í, â, ê, ô, à
- Palavras técnicas frequentes em PT-BR: `função`, `sessão`, `execução`, `ação`, `criação`, `não`, `próximo`, `último`, `diretório`, `descrição`, `validação`, `informação`, `aplicação`, `operação`, `conexão`, `exceção`, `solução`, `interação`, `produção`, `instalação`, `documentação`, `integração`

Exceções (palavras técnicas que ficam SEM acento por convenção):
- Chaves de dict como `"sessao"` (compatibilidade ASCII); marcar com `# noqa-acento` (ou variantes)
- Identificadores Python sem acento (PEP-8)
- IDs de sprint com acentos artificiais (`SPRINT_*_FIX_01`)

Validação local: `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths <spec.md>` deve retornar exit 0 antes de declarar spec pronto.
```

### `scripts/sanitize_spec_acentuacao.py` (NOVO)

```python
#!/usr/bin/env python3
"""Sanitiza acentuação PT-BR em specs de sprint do Nyx-Code.

Aplica regex de substituição em 20 palavras-padrão sem acento → versão acentuada.
Idempotente: rodar 2x produz mesmo arquivo.

Uso:
    python3 scripts/sanitize_spec_acentuacao.py <spec1.md> <spec2.md> ...
    python3 scripts/sanitize_spec_acentuacao.py --check <spec.md>  # dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SUBSTITUICOES = {
    r"\bnao\b": "não",
    r"\bsessao\b": "sessão",
    r"\bexecucao\b": "execução",
    r"\bacao\b": "ação",
    r"\bcriacao\b": "criação",
    r"\bproximo\b": "próximo",
    r"\bultimo\b": "último",
    r"\bdiretorio\b": "diretório",
    r"\bdescricao\b": "descrição",
    r"\bvalidacao\b": "validação",
    r"\binformacao\b": "informação",
    r"\baplicacao\b": "aplicação",
    r"\boperacao\b": "operação",
    r"\bconexao\b": "conexão",
    r"\bexcecao\b": "exceção",
    r"\bsolucao\b": "solução",
    r"\binteracao\b": "interação",
    r"\bproducao\b": "produção",
    r"\binstalacao\b": "instalação",
    r"\bdocumentacao\b": "documentação",
    r"\bintegracao\b": "integração",
    r"\bcanonica\b": "canônica",
    r"\bautomacao\b": "automação",
    r"\bautomatica\b": "automática",
    r"\bpermissoes\b": "permissões",
}


def sanitize(content: str) -> tuple[str, int]:
    """Retorna (conteudo_novo, num_substituicoes)."""
    total = 0
    novo = content
    for padrao, sub in SUBSTITUICOES.items():
        novo, n = re.subn(padrao, sub, novo, flags=re.IGNORECASE)
        total += n
    return novo, total


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Sanitiza acentuação PT-BR em specs de sprint."
    )
    parser.add_argument(
        "paths", nargs="+", type=Path, help="Arquivos .md de spec"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Apenas reporta sem modificar (dry-run)",
    )
    args = parser.parse_args(argv)

    rc = 0
    for path in args.paths:
        if not path.exists():
            print(f"[erro] {path}: não existe", file=sys.stderr)
            rc = 2
            continue
        original = path.read_text(encoding="utf-8")
        novo, n = sanitize(original)
        if n == 0:
            print(f"[ok] {path}: zero violações")
            continue
        if args.check:
            print(f"[check] {path}: {n} substituições propostas")
            rc = 1
        else:
            path.write_text(novo, encoding="utf-8")
            print(f"[fix] {path}: {n} substituições aplicadas")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

---

## Proof-of-work

```bash
# Antes
bash scripts/sprint_invariants.sh > /tmp/inv_before_planej.txt 2>&1

# Implementar (Edit no agente global + Write do script local)

# Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_planej.txt 2>&1

# Asserto template global tem regra
python3 -c 'from pathlib import Path; p = Path.home() / ".claude/agents/planejador-sprint.md"; t = p.read_text(); assert "PT-BR" in t and "acent" in t.lower(); print("OK template")'

# Asserto script local funciona
python3 scripts/sanitize_spec_acentuacao.py --help | head -5
python3 scripts/sanitize_spec_acentuacao.py --check dev-journey/06-sprints/producao/SPRINT_INFRA_PLANEJADOR_ACENTUACAO_AUTO_01.md
# (este spec deve ter 0 violações)

# Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/sanitize_spec_acentuacao.py
echo "rc=$?"
```

## Critério binário

- [ ] Template global tem invariante PT-BR
- [ ] scripts/sanitize_spec_acentuacao.py executável e idempotente
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
- [ ] MASTER 125jj PENDENTE → CONCLUIDA

---

*"O defensor antecede o ataque." — princípio preventivo*
