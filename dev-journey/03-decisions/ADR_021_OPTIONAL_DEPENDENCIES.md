# ADR-021 — Dependências opcionais

**Status:** ACEITO
**Data:** 2026-04-19
**Contexto da Onda:** 22, Bloco 2.5

## Contexto

O Nyx é Local First (ADR-001) e roda em hardware modesto (RTX 3050 Laptop 4GB, 16 GiB RAM). Algumas features agregam valor mas dependem de bibliotecas pesadas ou específicas de ambiente:

- **tree-sitter** (consumidor previsto: CTX-03, RepoMap via AST) -- parsers nativos em C, ~50 MB por linguagem, requer `tree-sitter-languages` compilado.
- **kitty graphics protocol** (consumidor previsto: render de imagens inline no REPL) -- funciona só no terminal kitty; em gnome-terminal ou xterm não tem efeito.

Exigir essas deps na instalação base violaria duas regras de ouro: (a) Local First ergonômico (o usuário não deve precisar compilar nada para rodar o REPL básico), e (b) graceful degradation (sistema deve funcionar sem a feature, não crashar).

## Decisão

Dependências que habilitam features avançadas são **opcionais** e seguem o padrão:

1. Detecção em import-time via `importlib.util.find_spec`, não via `try/except ImportError` dentro de função quente:

   ```python
   from importlib.util import find_spec

   HAS_TREE_SITTER = find_spec("tree_sitter") is not None
   HAS_KITTY_GRAPHICS = find_spec("kitty_graphics_protocol") is not None
   ```

2. Flag booleana módulo-level: `HAS_<FEATURE>`. Serve como contrato legível para qualquer consumidor (tool, service, render).

3. Feature consulta a flag e fornece **fallback explícito** (nunca crash, nunca silent no-op):
   - RepoMap sem tree-sitter → fallback textual via `ripgrep`/`grep`.
   - Render de imagem sem kitty → fallback ASCII ou mensagem `[imagem omitida: kitty não detectado]`.

4. README e `pyproject.toml` listam deps opcionais sob `[project.optional-dependencies]` (extras), com comando de instalação documentado.

5. Teste no Gauntlet cobre **os dois caminhos**: com a dep instalada (feature completa) e sem (fallback). Gauntlet roda no ambiente real, então a matriz é simples: uma fase com extras, outra sem.

## Consequências

Positivas:

- Instalação base permanece leve e portável (Local First ergonômico preservado).
- Sistema degrada gracefully em máquinas modestas, containers minimalistas, terminais não-kitty.
- Contrato `HAS_<FEATURE>` é documentação viva e testável.

Negativas:

- Código fica verboso (checagem de flag em cada feature).
- Teste exige cobrir dois caminhos (mitigação: Gauntlet aceita, já é design).
- Risco de fallback divergir da feature "completa" em comportamento sutil (mitigação: testes equivalentes em ambos caminhos, não apenas smoke).

## Alternativas consideradas

**Alt A: `try/except ImportError` dentro de cada função consumidora.**
- Contra: checagem re-executada a cada chamada; import já cacheado, mas API fica poluída.
- Contra: `HAS_<FEATURE>` precisa ser recomputada em cada call-site -- não escala.
- Rejeitada em favor de `find_spec` + flag módulo-level.

**Alt B: dep obrigatória com fallback em runtime.**
- Contra: bloat da instalação base; usuário com terminal não-kitty ainda precisa baixar lib inútil.
- Contra: viola Local First ergonômico.
- Rejeitada.

**Alt C: apenas `extras_require` sem detecção runtime.**
- Aceitável como complemento, mas não substitui a detecção: o código precisa saber em runtime se a dep veio junto ou não.
- Adotada **em conjunto** com a Decisão, não como substituta.

## Exemplos canônicos

| Dep opcional | Flag | Consumidor (sprint) | Fallback |
|---|---|---|---|
| `tree_sitter` + `tree_sitter_languages` | `HAS_TREE_SITTER` | CTX-03 (RepoMap AST) | RepoMap textual via `rg` |
| `kitty_graphics_protocol` | `HAS_KITTY_GRAPHICS` | VISION-01/render futuro | ASCII art ou placeholder textual |

Futuras deps opcionais seguem o mesmo padrão sem ADR nova (este ADR é o registro do padrão, não da dep específica).

## Referências

- ADR-001 Local First.
- ADR-013 Integração Obrigatória.
- ADR-015 Documentação para continuidade.
- Sprint CTX-03 (primeiro consumidor real).
- Sprint VISION-01 (segundo consumidor previsto, via ADR-022).

*"Tudo que não é essencial é luxo; tudo que é luxo deve ser opcional." -- Epicteto (paráfrase)*
