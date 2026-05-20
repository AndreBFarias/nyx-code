# SPRINT RUFF-EXTERNAL-NOQA-CONFIG-01

**Status:** CONCLUIDA (com investigação documentada — warnings cosméticos persistem por design do ruff)
**Data:** 2026-05-19 (terceira sessão, ~23h48)

## Contexto

Múltiplas linhas no projeto usam marker customizado `# noqa-acento` (do `~/.config/zsh/scripts/validar-acentuacao.py`) para suprimir falsos positivos do validador externo de acentuação em palavras técnicas (chaves de dict como `"sessao"`, tokens linguísticos como `"nao"` em regex, etc.). Ruff emite ~23 warnings cosméticos `Invalid noqa directive` para essas linhas.

## Investigação

Configuração proposta: `[tool.ruff.lint] external = ["noqa-acento"]` em `pyproject.toml`.

**Resultado**: configuração adicionada mas **warnings persistem**. Análise do comportamento real do ruff:

- `external` silencia apenas CÓDIGOS custom desconhecidos (formato `# noqa: XYZ123` onde XYZ123 não é regra do ruff).
- `# noqa-acento` é **sintaxe malformada** (falta `:` após `noqa`), tratada pelo ruff antes do check de external.
- Por isso `external = ["noqa-acento"]` não tem efeito sobre os warnings.

## Decisão

Aceitar tradeoff:
- Warnings cosméticos persistem (~23 ocorrências em nyx/ + scripts/)
- Ruff exit code permanece 0 — invariante #10 do projeto verifica exit code, não warnings
- Não impede produção, gate v1.0 ou qualquer fluxo

Solução alternativa que NÃO foi implementada (deferida):
- Trocar marker `# noqa-acento` por `# noqa: ACENTO` em todos arquivos + atualizar `~/.config/zsh/scripts/validar-acentuacao.py` para aceitar ambos formatos
- Out-of-scope: requer mudança em arquivo fora do repo
- Sprint hipotética futura: `NOQA-ACENTO-RENAME-01` (BAIXA, opcional)

## Touches

- `pyproject.toml:53-60`: adicionado `external = ["noqa-acento"]` com comentário explicativo documentando que silencia apenas códigos custom (não sintaxe malformada)

## Proof-of-work

- `python3 -m ruff check nyx/ scripts/` -> All checks passed! (exit 0)
- Warnings cosméticos persistem mas não bloqueiam nada
- `bash scripts/sprint_invariants.sh` -> 14/14 PASS

---

*"Investigar antes de aceitar; aceitar quando o custo da limpeza supera o ganho." -- RUFF-EXTERNAL-NOQA-CONFIG-01*
