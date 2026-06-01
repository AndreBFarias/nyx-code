# SPRINT ONDA-38-B — ONBOARDING-REPLAY-FLAG-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: ONBOARDING-REPLAY-FLAG-01
  title: "Flag --onboarding que força o wizard de primeiro uso mesmo com .first_run_done presente"
  onda: 38
  prioridade: MEDIA
  tipo: Feature
  depende_de_ordem: ONBOARDING-IMPROVE-02 deve rodar DEPOIS desta (ambas tocam onboarding.py)
  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "novo case --onboarding que faz exec direto de cli.py --onboarding (padrão do --smoke L148-151)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "novo arg --onboarding em main() que força run_first_run_wizard ignorando o marker + imprime config.toml ao fim"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "parametrizar force no wizard para re-perguntar nome mesmo com config.toml persistido"
  acceptance_criteria:
    - "./run.sh --onboarding re-dispara o wizard mesmo com ~/.nyx/.first_run_done presente"
    - "ao final, imprime as chaves persistidas de ~/.nyx/config.toml"
    - "fluxo normal (sem flag) permanece byte-a-byte inalterado"
    - "smoke boot ok + invariantes 14/14"
```

---

**Status:** CONCLUIDA (2026-06-01 — run_first_run_wizard(force=True) + helper read_persisted_config em onboarding.py; arg --onboarding em cli.py + dispatch que ecoa config.toml; case --onboarding em run.sh. Proof: ./run.sh --onboarding ecoa config real (read-only); harness real comprova force=True re-pergunta+persiste e force=False intacto; smoke boot ok, invariantes 14/14, acentuação exit 0. Teste pytest pulado por ADR-014 (testes só via Gauntlet); prova via runtime real.)
**Data criação:** 2026-06-01
**Modelo obrigatório:** sem subagentes (Read/Grep/Glob direto)

---

## Contexto

Hoje o wizard de primeiro uso só roda na primeira execução: `should_run_tutorial` (`onboarding.py:156-162`) retorna `False` se `~/.nyx/.first_run_done` existe. Não há forma de re-rodar o onboarding deliberadamente para reconfigurar nome/aesthetic/schema/modelo. Esta sprint adiciona um modo de replay explícito via flag, que força o wizard e ao final ecoa o estado persistido em `~/.nyx/config.toml`.

## Escopo (touches autorizados)

- Arquivos a modificar:
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/run.sh` (bloco `case` em L146-238)
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py` (parser em `main()` L631-655 + bloco de dispatch L657-678)
  - `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py` (`run_first_run_wizard` L174-244)
- Arquivos a criar: nenhum
- Arquivos NÃO a tocar:
  - `nyx/cli.py` ESTÁ no conjunto protegido do check #14. As edições são só no parser/dispatch; não tocar os glifos U+25xx.

## Observação sobre a hipótese original (ajuste do planejador)

Verificado via leitura:

- `should_run_tutorial` está em `onboarding.py:156-162` (confere).
- `run_first_run_wizard` está em `onboarding.py:174-244` (confere). PORÉM ele tem dois gates internos que o force precisa contornar:
  1. `if not sys.stdin.isatty(): mark_done(); return` (L193-195) — em replay interativo isto NÃO atrapalha (tty presente), mas o modo precisa permanecer não-interativo-seguro.
  2. O passo 01/07 (nome) SÓ pergunta se `_read_persisted_user_name()` retornar vazio (L198-210). Com `.first_run_done` presente normalmente já há nome persistido, então o force precisa de um parâmetro para RE-perguntar o nome. Sem isso, o replay pularia o passo 01/07 silenciosamente.
- O case do run.sh: `--smoke` (L148-151) usa `exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --smoke`. Padrão a replicar para `--onboarding`.
- O bloco `*)` (L234) repassaria `--onboarding` desconhecido para `EXTRA_ARGS`, mas `EXTRA_ARGS` NÃO é passado ao exec final de cli.py (L873 roda `cli.py` sem args). Portanto um case dedicado com `exec` é necessário.

## Acceptance criteria

1. `./run.sh --onboarding` dispara o wizard MESMO com `~/.nyx/.first_run_done` presente.
2. O passo de nome (01/07) é re-perguntado no modo replay (não pulado).
3. Ao final do wizard, o cli imprime as chaves de `~/.nyx/config.toml` (uma por linha, formato `chave = valor`).
4. `cli.py` sem a flag mantém comportamento idêntico ao atual (`should_run_tutorial` inalterado para o fluxo normal).
5. `./run.sh --smoke` imprime `boot ok`, exit 0.
6. `bash scripts/sprint_invariants.sh` PASS 14/14, FAIL 0.

## Invariantes a preservar

- Idempotência do marker: o replay NÃO deve apagar `.first_run_done`; só re-roda o wizard por cima e re-marca (já idempotente via `mark_done`).
- Persistência merge não-destrutivo: `_persist_user_name` (`onboarding.py:44-73`) já preserva chaves existentes; o replay reusa essa função.
- Check #14 anti-sanitizer: glifos U+25xx em `cli.py` intactos.
- GUIDE.md §2 simplicidade: o modo replay reusa `run_first_run_wizard`; não duplica a sequência de 7 passos.

## Plano de implementação

1. `onboarding.py`: dar a `run_first_run_wizard` um parâmetro `force: bool = False`. Quando `force=True`, o passo 01/07 re-pergunta o nome mesmo havendo `_read_persisted_user_name()` (ignora o atalho `if persisted:` da L198-200).
2. `onboarding.py`: adicionar helper público `read_persisted_config() -> dict` que lê `~/.nyx/config.toml` via `tomllib` e retorna o dict (reaproveita o padrão de `_read_persisted_user_name`). Retorna `{}` se ausente.
3. `cli.py` (parser): `parser.add_argument("--onboarding", action="store_true", help="Re-roda o wizard de primeiro uso (replay) e imprime o config persistido.")`.
4. `cli.py` (dispatch, antes do bloco headless/repl): se `args.onboarding`, importar `run_first_run_wizard` + `read_persisted_config`, chamar `run_first_run_wizard(force=True)`, depois imprimir cada par `chave = valor` do `read_persisted_config()`, e `sys.exit(0)`.
5. `run.sh`: novo case `--onboarding)` no `while` (L146-238), seguindo o padrão do `--smoke`: `exec "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/nyx/cli.py" --onboarding`.
6. Rodar smoke + invariantes.

## Testes

- Adicionar teste unitário em `tests/` (localizar o arquivo de testes de onboarding via `rg -l "onboarding" tests/`) cobrindo: `run_first_run_wizard(force=True)` re-pergunta nome quando há nome persistido (mockar `sys.stdin.isatty()` e `_timed_input`), e `read_persisted_config()` retorna o dict de um config.toml de fixture.
- Baseline: FAIL_BEFORE = 0 (invariantes), esperado FAIL_AFTER = 0.

## Proof-of-work esperado

- Diff final dos 3 arquivos.
- Runtime real:
  - Replay: `./run.sh --onboarding` com `~/.nyx/.first_run_done` PRESENTE — comprovar que o wizard re-dispara (não pula) e que ao final imprime o conteúdo de `~/.nyx/config.toml`. Capturar a saída do terminal.
  - Smoke: `./run.sh --smoke` (`boot ok`, exit 0)
  - Invariantes: `bash scripts/sprint_invariants.sh` (14/14)
- Cleanup pós-teste com modelo (se o wizard subir algo): `pkill -f "nyx/proxy.py"`, `pkill -f "ollama serve"`, `nvidia-smi` confirmando VRAM livre (BRIEF check #5). O wizard de onboarding em si NÃO precisa de modelo carregado.
- Acentuação periférica: `python3 /home/andrefarias/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli.py nyx/agent/onboarding.py` exit 0.
- Hipótese verificada: `rg -n "should_run_tutorial|run_first_run_wizard|--onboarding|read_persisted_config" nyx/cli.py nyx/agent/onboarding.py run.sh`.

## Riscos e não-objetivos

- Não-objetivo: redesenhar os 7 passos do wizard (isso é a sprint ONBOARDING-IMPROVE-02 — bloco C).
- Risco de ordem: B e C tocam `onboarding.py`. Declarado: B roda ANTES de C (C absorve o `force` introduzido aqui na revisão dos passos). NÃO rodar B e C em paralelo.
- Risco: replay em ambiente não-tty (CI) deve continuar a fazer `mark_done()` e retornar sem travar — preservar o gate `not sys.stdin.isatty()`.

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Precedente: ONBOARDING-01 (linha 313 do MASTER, CONCLUIDA) — wizard original; TUI-REDESIGN-26-05 (config.toml como fonte de nome)

---

*"Reconfigurar deve ser tão fácil quanto a primeira vez."*
