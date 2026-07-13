## 0. SPEC (machine-readable)

```yaml
sprint:
  id: WIZARD-CONFIG-EFFECTIVE-01
  numero: 436
  title: "Wizard efetivo: as 7 escolhas persistidas em config.toml passam a valer no boot (schema único, parser <3.11, /config setup com merge)"
  onda: 48
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []
  absorve: []
  relacionada: [403]  # MODEL-SWAP-REAL-OR-HONEST-01 cobre a troca em RUNTIME; esta cobre a adocao no BOOT

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "_load_toml_overrides passa a usar o parser compartilhado (le config.toml tambem em <3.11); load_settings aplica as chaves visuais do wizard em os.environ (se ausentes no env) ANTES da resolucao de tema; unificar a chave do modelo em `modelo`"
      linhas_alvo: "49-66 (_load_toml_overrides), 77-79 (leitura do modelo), 108-129 (bloco antes do return NyxSettings)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "_read_persisted_user_name e read_persisted_config passam a usar o parser compartilhado -- o nome escolhido carrega tambem no Python 3.10 (Ubuntu 22.04)"
      linhas_alvo: "24-58 (_read_persisted_user_name, read_persisted_config), 61-125 (persist_config_key ja e o writer de merge canônico -- reusar)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_handlers.py
      reason: "_handle_config_setup para de sobrescrever o arquivo inteiro; grava chave a chave via persist_config_key (merge não-destrutivo) preservando user_display_name/aesthetic/entity/schema/banner_mode/auto_approve"
      linhas_alvo: "625-664 (_handle_config_setup, bloco content + tmp.replace)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "o wizard passa a persistir o modelo sob a chave canônica `modelo` (hoje grava `model`, que nenhum leitor consome); sem mudar o texto do passo nem o env-export NYX_MODEL"
      linhas_alvo: "266 (cfg[model] = ask), 160-170 (write_config), 172-186 (emit_env_exports)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "MODEL adota o `modelo` persistido em ~/.nyx/config.toml quando NYX_MODEL não esta no ambiente (hoje ignora o toml e cai direto no default hardcoded)"
      linhas_alvo: "134 (MODEL=${NYX_MODEL:-qwen2.5-coder:3b})"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/config_file.py
      reason: "fonte unica do schema de config.toml: parser minimo (tomllib em >=3.11, parser de linha `chave = valor` em <3.11) + constante WIZARD_ENV_KEYS (chave-toml -> env NYX_*). Importado por settings, onboarding e cli_handlers"
  removes: []

  forbidden:
    - "Adicionar emoji"
    - "Usar 'print()' fora de cli.py/output.py/cli_handlers.py"
    - "Mencao a IA proprietaria"
    - "Fazer o config.toml SOBRESCREVER env vars ja setadas (precedencia: env de CLI/flag > config.toml > default) -- config.toml so preenche o que o env não trouxe"
    - "Alterar a semantica de troca de modelo em RUNTIME (escopo da sprint 403); esta sprint so trata a ADOCAO no boot"
    - "Tocar a leitura de extra_roots/ollama_port/proxy_port (ja funcionam via toml_cfg) exceto para trocar a fonte pelo parser compartilhado byte-equivalente"
    - "Introduzir dependencia externa (tomli/tomli-w) no requirements -- o parser <3.11 e vendorizado em config_file.py (stdlib apenas)"
    - "Mudar o texto/idioma dos passos do wizard ou das perguntas do /config setup"

  tests:
    - cmd: "/home/andrefarias/.local/bin/ruff check nyx/config/config_file.py nyx/config/settings.py nyx/agent/onboarding.py nyx/cli_handlers.py scripts/menu_wizard.py"
      deve_passar: true
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/config/config_file.py nyx/config/settings.py nyx/agent/onboarding.py nyx/cli_handlers.py scripts/menu_wizard.py"
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: true
    - cmd: "./run.sh --smoke"
      deve_passar: true

  acceptance_criteria:
    - "AC1 (chaves visuais valem no boot): apos load_settings(), com um ~/.nyx/config.toml contendo aesthetic/entity/schema/banner_mode/auto_approve, os respectivos NYX_AESTHETIC/NYX_ENTITY/NYX_SCHEMA/NYX_BANNER_MODE/NYX_AUTO_APPROVE ficam setados em os.environ (quando o env não os trouxe), de modo que theme_manager/design_tokens_extended/cli_headless leem a escolha do wizard e não o default"
    - "AC2 (schema único do modelo): o wizard persiste o modelo sob a chave `modelo` (não mais `model`); settings.py continua lendo `modelo`; um config.toml gerado pelo wizard passa a ter o modelo efetivamente lido no boot"
    - "AC3 (config le em <3.11): _load_toml_overrides e _read_persisted_user_name usam o parser compartilhado; com Python 3.10 e um config.toml valido, load_settings devolve o modelo persistido e _read_persisted_user_name devolve o nome (hoje ambos retornam vazio/None em <3.11)"
    - "AC4 (/config setup não destroi): _handle_config_setup grava via merge (persist_config_key), preservando user_display_name e as chaves visuais do wizard; rodar /config setup depois do wizard não apaga o nome nem a estetica escolhida"
    - "AC5 (run.sh adota o modelo do boot): com NYX_MODEL ausente do ambiente e `modelo = \"qwen2.5-coder:7b\"` em ~/.nyx/config.toml, o MODEL do run.sh assume qwen2.5-coder:7b (não o default hardcoded); NYX_MODEL no ambiente continua tendo precedencia"
    - "AC6 (precedencia respeitada): env var vinda de flag de CLI (ex.: ./run.sh --aesthetic X exporta NYX_AESTHETIC) continua vencendo o config.toml -- o boot so preenche a env a partir do toml quando ela esta ausente"
    - "AC7 (higiene): ruff limpo nos arquivos tocados, acentuacao rc=0, invariantes FAIL_AFTER <= FAIL_BEFORE, smoke boot 'boot ok'"
```

---

# Sprint WIZARD-CONFIG-EFFECTIVE-01 — Wizard efetivo: a config do primeiro uso passa a valer no boot

**Status:** PENDENTE
**Data criação:** 2026-07-12
**Executor:** modelo-cerebro autorizado pelo dono nesta onda (ver EXECUTAR_SPRINT.md)

---

## Contexto do projeto (snapshot — não referência)

> **Missão (calibração):** o Nyx-Code faz o pior LLM local (`qwen2.5-coder:3b`) na pior máquina possível parecer um agente de código profissional offline. A robustez pertence à INFRA, não ao modelo (ADR-032/033/034). O usuário-alvo é leigo e sem hardware bom — tipicamente Ubuntu 22.04, cujo `python3` é o 3.10. É exatamente esse público que hoje passa pelo wizard, responde 7 perguntas, vê "configuração salva" e no boot seguinte encontra tudo de volta ao default. Onboarding que mente quebra a confiança logo no primeiro minuto.
>
> **ADRs relevantes (inline):**
> - **ADR-032/033 (A INFRA CARREGA / ENFORCEMENT, NÃO CONFIANÇA):** o que a UI promete ("persiste, próximo boot já adota") a infra tem de cumprir; uma promessa de persistência sem leitura no boot é um sucesso fabricado.
> - ADR-001 (Local First), ADR-009.
>
> **Estado (2026-07-12):** `qwen2.5-coder:3b`. Portes: Ollama `11435`, proxy `11436` (`nyx/config/defaults.py`). Harness de portabilidade oficial usa Python 3.10 (`docker/Dockerfile.clean-boot`).

---

## Problema

O wizard de primeiro uso (7 escolhas: nome, aesthetic, entidade, schema, banner, modelo, auto-approve) grava tudo em `~/.nyx/config.toml`, mostra "configuração salva" e o README promete (linha 120): *"Persiste em `~/.nyx/config.toml`. Próximo boot já adota."* Na prática **nenhum boot seguinte lê a maior parte dessas chaves**. São três faces do mesmo mecanismo — config.toml sem fonte única de schema, com escritores e leitores divergentes, e um leitor travado em Python 3.11+:

**Face 1 — chaves sem leitor / chave trocada (ALTA).** O wizard grava `cfg["model"]` (`scripts/menu_wizard.py:266`, escrito por `write_config`), mas `nyx/config/settings.py:79` lê OUTRA chave: `model = os.getenv("NYX_MODEL") or toml_cfg.get("modelo") or defaults.DEFAULT_MODEL`. As chaves visuais (`aesthetic`, `entity`, `schema`, `banner_mode`, `auto_approve`) não têm leitor de config algum: `nyx/config/defaults.py:42-43`, `nyx/themes/design_tokens_extended.py`, `nyx/themes/theme_manager.py`, `nyx/cli_boot.py:58` e `nyx/cli_headless.py:58` só leem **env vars** (`NYX_AESTHETIC` etc). E no first-run os exports nem são emitidos: `scripts/menu_wizard.py:293` guarda o `emit_env_exports` atrás de `os.environ.get("NYX_MENU_EMIT") == "1" and not is_first_run`. Resultado: o `config.toml` é escrito mas as env vars do processo nunca recebem os valores.

**Face 2 — config ilegível em <3.11 (MEDIA).** `nyx/config/settings.py:53-54` faz `if sys.version_info < (3, 11): return {}` e `nyx/agent/onboarding.py:33` importa `tomllib` (3.11+) dentro de `try/except Exception`, então `_read_persisted_user_name` retorna sempre `None` no 3.10. Mas `install.sh:160` aceita 3.10 e `pyproject.toml:11` declara `requires-python = ">=3.10"`. No Ubuntu 22.04 até a ÚNICA chave que tem leitor (`user_display_name`) falha em silêncio: a pessoa diz como quer ser chamada e a Nyx a chama de "visitante" para sempre.

**Face 3 — /config setup destrói o arquivo (MEDIA).** `nyx/cli_handlers.py:653-664` monta um `content` do zero (`modelo`/`tema`/`bypass`/`ctx_limit`) e faz `tmp.replace(config_path)` — reescreve o arquivo inteiro, apagando `user_display_name` e todas as chaves visuais. E o onboarding orienta explicitamente ajustes manuais via `/config setup` quando o wizard é cancelado, ou seja, seguir a orientação apaga o nome. Note que `nyx/agent/onboarding.py:93` já tem `persist_config_key`, um writer de **merge não-destrutivo**; o handler simplesmente não o usa.

O comum às três: não há **uma** definição de quais chaves existem no `config.toml` nem quem as lê; a leitura depende de `tomllib`; e há escritores incompatíveis (`model` vs `modelo`, overwrite vs merge).

---

## Causa-raiz (verificada no código)

Evidências reconferidas em 2026-07-12 (linhas podem ter deslizado desde o briefing — reconferidas aqui):

- `scripts/menu_wizard.py:266` — `cfg["model"] = ask("Modelo Ollama", ...)`. **Confirmado.** `write_config` (linhas 160-170) itera `merged.items()` e escreve `model = "..."`. `emit_env_exports` (172-186) lê `cfg["model"]` e imprime `export NYX_MODEL=...` — mas só é chamado quando `NYX_MENU_EMIT=1 and not is_first_run` (293).
- `nyx/config/settings.py:79` — `model = os.getenv("NYX_MODEL") or toml_cfg.get("modelo") or defaults.DEFAULT_MODEL`. **Confirmado**: lê `modelo`, não `model`. As únicas chaves lidas de `toml_cfg` são `modelo` (79), `ollama_port` (81), `proxy_port` (86), `extra_roots` (117). As visuais não aparecem.
- `nyx/config/settings.py:53-54` — `if sys.version_info < (3, 11): return {}`. **Confirmado.**
- Leitores das chaves visuais só olham env: `nyx/config/defaults.py:42-43`, `nyx/themes/design_tokens_extended.py:308-323`, `nyx/themes/theme_manager.py:29-81`, `nyx/cli_boot.py:58`, `nyx/cli_headless.py:58`. **Confirmado via grep** — nenhum `.get("aesthetic")`/`.get("entity")`/`.get("schema")`/`.get("banner_mode")`/`.get("auto_approve")` fora do próprio `menu_wizard.py`.
- `nyx/cli_handlers.py:653-664` — `content = (...)` seguido de `tmp.replace(config_path)`. **Confirmado overwrite.** `persist_config_key` existe em `nyx/agent/onboarding.py:93-125` (writer de merge). `_handle_config_setup` começa em `nyx/cli_handlers.py:625`.
- `run.sh:134` — `MODEL="${NYX_MODEL:-qwen2.5-coder:3b}"`; `run.sh:672` — `export OPENAI_MODEL="$MODEL"`. **Confirmado**: o `MODEL` nunca consulta o `config.toml`.
- `README.md:120` — "Persiste em `~/.nyx/config.toml`. Próximo boot já adota." **Confirmado.** `nyx/agent/tui/app.py:737` mostra "aplicado e salvo". **Confirmado.**

**Divergências do briefing (registradas):**
1. O briefing cita `onboarding.py` sem caminho; o arquivo real é `nyx/agent/onboarding.py` (não `nyx/onboarding.py`).
2. O briefing aponta `onboarding.py:34 import tomllib`; a linha real é `nyx/agent/onboarding.py:33` (deslize de 1). `persist_config_key` está em `:93` (bate).
3. `nyx/config/settings.py` também importa `tomllib` internamente (linha 56, dentro de `_load_toml_overrides`) — o mesmo gargalo de <3.11 vale para ele. Sem impacto no diagnóstico; reforça a Face 2.

Nenhuma divergência altera o mecanismo nem o fix. As três faces são o MESMO mecanismo (schema de config.toml sem fonte única + leitor travado em 3.11), por isso uma sprint com ACs separados.

---

## Solução proposta

Uma fonte única de schema + leitor robusto, e alinhar os escritores. Mínimo e cirúrgico:

1. **Criar `nyx/config/config_file.py`** (fonte única, stdlib apenas):
   - `CONFIG_PATH = Path.home() / ".nyx" / "config.toml"`.
   - `read_config_dict() -> dict`: usa `tomllib` em Python >=3.11; em <3.11 usa um parser de linha mínimo (`chave = valor`, com `"aspas"`, `true/false`, inteiros) — o formato que o próprio projeto grava (`write_config`/`persist_config_key` emitem exatamente `chave = valor` linha a linha). Retorna `{}` em ausência/erro (best-effort, não derruba boot).
   - `WIZARD_ENV_KEYS`: mapa `chave-toml -> nome de env NYX_*` para as chaves visuais: `{"aesthetic": "NYX_AESTHETIC", "entity": "NYX_ENTITY", "schema": "NYX_SCHEMA", "banner_mode": "NYX_BANNER_MODE"}` mais o booleano `auto_approve -> NYX_AUTO_APPROVE` (mapeado para `"1"` quando verdadeiro). Chave canônica do modelo: `modelo`.
   - `apply_config_to_env(cfg: dict) -> None`: para cada chave em `WIZARD_ENV_KEYS`, se a env correspondente estiver **ausente** de `os.environ` e a chave existir em `cfg`, seta a env. **Nunca sobrescreve** env já presente (preserva precedência flag/CLI > config.toml).

2. **`nyx/config/settings.py`**: `_load_toml_overrides` passa a delegar em `read_config_dict()` (elimina o gate `< (3, 11)`); logo após obter `toml_cfg` em `load_settings`, chamar `apply_config_to_env(toml_cfg)` **antes** do return (e antes de qualquer resolução de tema — `load_settings` é chamado em `nyx/cli.py:115`, cedo no boot). A leitura do modelo segue em `modelo` (sem mudança).

3. **`nyx/agent/onboarding.py`**: `_read_persisted_user_name` e `read_persisted_config` passam a usar `read_config_dict()` — o nome carrega no 3.10. `persist_config_key` (o writer de merge) é reusado como está.

4. **`nyx/cli_handlers.py`**: `_handle_config_setup` troca o bloco `content = (...) / tmp.replace(...)` por chamadas a `persist_config_key("modelo", modelo)`, `persist_config_key("tema", tema)`, `persist_config_key("bypass", bypass)`, `persist_config_key("ctx_limit", ctx_limit)` — merge não-destrutivo. O backup `.toml.bak` (já feito nas linhas 632-635) permanece.

5. **`scripts/menu_wizard.py`**: o wizard persiste o modelo sob `modelo`. Edição mínima: em `write_config`, remapear a chave `model -> modelo` na escrita (ou renomear `cfg["model"]` para `cfg["modelo"]` na origem e ajustar o único outro leitor, `emit_env_exports`). O texto do passo e o `export NYX_MODEL` não mudam.

6. **`run.sh`**: antes de fixar `MODEL`, se `NYX_MODEL` estiver ausente do ambiente e `~/.nyx/config.toml` tiver `modelo = "..."`, adotar esse valor; senão, o default hardcoded. Leitura simples via `grep`/`sed` do padrão `^modelo = "..."` (não precisa do parser Python). `NYX_MODEL` no ambiente continua com precedência.

Com (1)+(2) as chaves visuais e o modelo do wizard passam a valer no boot Python; (3) conserta o nome no 3.10; (4) para de destruir a config; (5) alinha o escritor do wizard ao schema; (6) leva o modelo persistido ao proxy no boot.

---

## Aritmética

Sem meta de tamanho (`arquivo < NNNL`). Fix aditivo distribuído: 1 arquivo novo (`nyx/config/config_file.py`, estimado 40-60L: parser de linha ~15L + mapa + `apply_config_to_env`) e 5 arquivos editados com net-add pequeno cada (settings ~ +5L de delegação/chamada; onboarding troca 2 leitores pelo helper, net ~ -6L; cli_handlers troca ~12L de overwrite por ~4 chamadas de merge, net ~ -8L; menu_wizard ~ +2L de remapeamento; run.sh ~ +3L). Nenhum arquivo cruza limite de tamanho. O único número relevante é: **quantidade de arquivos tocados = 5 + 1 criado** (dentro do limite 5-8 de coesão arquitetural).

---

## Comandos de verificação (literais, copy-paste)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estatica + acentuacao (ruff via binario direto -- não ha modulo ruff no venv, ver BRIEF)
/home/andrefarias/.local/bin/ruff check nyx/config/config_file.py nyx/config/settings.py \
  nyx/agent/onboarding.py nyx/cli_handlers.py scripts/menu_wizard.py
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/config/config_file.py \
  nyx/config/settings.py nyx/agent/onboarding.py nyx/cli_handlers.py scripts/menu_wizard.py

# 2. Reconferir as ancoras (linhas podem ter deslizado):
rg -n 'cfg\["model"\]|toml_cfg.get\("modelo"\)|sys.version_info < \(3, 11\)|tmp.replace\(config_path\)|MODEL="\$\{NYX_MODEL' \
  scripts/menu_wizard.py nyx/config/settings.py nyx/cli_handlers.py run.sh

# 3. PROOF AC1+AC2+AC6 (chaves visuais + modelo valem no boot, sem GPU): grava um
#    config.toml de teste num HOME temporario, roda load_settings e verifica env + model.
./venv/bin/python - <<'PY'
import os, tempfile, pathlib
tmp = tempfile.mkdtemp()
os.environ["HOME"] = tmp
cfgdir = pathlib.Path(tmp) / ".nyx"; cfgdir.mkdir(parents=True)
(cfgdir / "config.toml").write_text(
    'user_display_name = "Andre"\n'
    'aesthetic = "cyberpunk"\n'
    'entity = "eris"\n'
    'schema = "compact"\n'
    'banner_mode = "neofetch"\n'
    'auto_approve = true\n'
    'modelo = "qwen2.5-coder:7b"\n', encoding="utf-8")
for k in ("NYX_AESTHETIC","NYX_ENTITY","NYX_SCHEMA","NYX_BANNER_MODE","NYX_AUTO_APPROVE","NYX_MODEL"):
    os.environ.pop(k, None)
from nyx.config.settings import load_settings
s = load_settings()
assert os.environ.get("NYX_AESTHETIC") == "cyberpunk", os.environ.get("NYX_AESTHETIC")
assert os.environ.get("NYX_ENTITY") == "eris"
assert os.environ.get("NYX_SCHEMA") == "compact"
assert os.environ.get("NYX_BANNER_MODE") == "neofetch"
assert os.environ.get("NYX_AUTO_APPROVE") == "1"
assert s.model == "qwen2.5-coder:7b", s.model
# AC6: env pre-existente vence o toml
os.environ["NYX_AESTHETIC"] = "brutalist"
from importlib import reload
import nyx.config.settings as _s; reload(_s)
_s.load_settings()
assert os.environ.get("NYX_AESTHETIC") == "brutalist"
print("OK AC1/AC2/AC6: chaves visuais + modelo do wizard valem no boot; env de flag vence o toml")
PY

# 4. PROOF AC3 (parser <3.11, sem GPU): o parser de linha le sem tomllib.
./venv/bin/python - <<'PY'
import nyx.config.config_file as cf
# forca o caminho do parser de linha independente da versao instalada
d = cf._parse_toml_lines('user_display_name = "Andre"\nmodelo = "qwen2.5-coder:7b"\nauto_approve = true\n')  # noqa
assert d.get("user_display_name") == "Andre", d
assert d.get("modelo") == "qwen2.5-coder:7b", d
assert d.get("auto_approve") is True, d
print("OK AC3: parser de linha (fallback <3.11) le nome/modelo/booleano sem tomllib")
PY
#    (o nome do helper interno pode variar -- ver criterio de aceite; se o executor
#     nomear diferente, ajustar a chamada. O contrato e: existe um caminho de leitura
#     que não depende de tomllib.)

# 5. PROOF AC4 (/config setup faz merge, sem GPU): simula o handler preservando o nome.
#    (Executar com o HOME temporario do passo 3, ou inspecionar via persist_config_key
#     direto: persistir user_display_name, depois persistir modelo, e confirmar que
#     o nome sobrevive.)
./venv/bin/python - <<'PY'
import os, tempfile, pathlib
tmp = tempfile.mkdtemp(); os.environ["HOME"] = tmp
(pathlib.Path(tmp) / ".nyx").mkdir(parents=True)
from nyx.agent.onboarding import persist_config_key, read_persisted_config
persist_config_key("user_display_name", "Andre")
persist_config_key("aesthetic", "cyberpunk")
persist_config_key("modelo", "qwen2.5-coder:7b")   # simula /config setup pos-wizard
cfg = read_persisted_config()
assert cfg.get("user_display_name") == "Andre", cfg
assert cfg.get("aesthetic") == "cyberpunk", cfg
print("OK AC4: escrita de chave por merge preserva nome + estetica do wizard")
PY

# 6. PROOF AC5 (run.sh adota o modelo do toml, sem GPU/serve): so a resolucao do MODEL.
#    HOME temporario com config.toml, NYX_MODEL ausente -> MODEL deve virar 7b.
#    (Rodar o trecho de resolucao de MODEL isolado, ou `bash -x` capturando a linha do
#     MODEL. não subir Ollama/proxy -- a prova e a atribuicao da variavel, não o serve.)

# 7. Invariantes + smoke
bash scripts/sprint_invariants.sh
./run.sh --smoke
```

> **Nota GPU:** os passos 3-6 rodam SEM Ollama/GPU (config em HOME temporário; nenhuma inferência). A prova de que o modelo persistido é de fato SERVIDO pelo proxy no boot (end-to-end com `qwen2.5-coder:7b` respondendo) exige GPU exclusiva e fica **DEFERIDA para GPU exclusiva** — executar só quando `pgrep -af "Luna.*driver|valida_sprint"` estiver vazio (protocolo anti-contenção do BRIEF), como as specs 403/407.

---

## Critério binário de aceite (IA executora)

- [ ] `nyx/config/config_file.py` criado: `read_config_dict()` lê `config.toml` em >=3.11 (tomllib) E em <3.11 (parser de linha stdlib); `WIZARD_ENV_KEYS` mapeia as chaves visuais para `NYX_*`; `apply_config_to_env` só preenche env ausente
- [ ] `settings.py`: `_load_toml_overrides` sem o gate `< (3, 11)` (usa `read_config_dict`); `load_settings` chama `apply_config_to_env(toml_cfg)` antes do return; modelo segue em `modelo`
- [ ] `onboarding.py`: `_read_persisted_user_name` e `read_persisted_config` usam `read_config_dict` (nome carrega no 3.10)
- [ ] `cli_handlers.py`: `_handle_config_setup` grava via `persist_config_key` (merge), sem `tmp.replace` do arquivo inteiro; backup `.toml.bak` mantido
- [ ] `menu_wizard.py`: modelo persistido sob a chave `modelo`; texto do passo e `export NYX_MODEL` intactos
- [ ] `run.sh`: `MODEL` adota `modelo` do `config.toml` quando `NYX_MODEL` ausente; `NYX_MODEL` no ambiente ainda vence
- [ ] Proofs runtime-reais colados: passo 3 (AC1/AC2/AC6), passo 4 (AC3), passo 5 (AC4); passo 6 (AC5) colado ou justificado; end-to-end de serve DEFERIDO GPU
- [ ] `ruff` limpo, acentuação rc=0, `FAIL_AFTER <= FAIL_BEFORE`, `./run.sh --smoke` = `boot ok`
- [ ] `SPRINT_ORDER_MASTER.md` marca 436 CONCLUIDA; spec movida para `concluidos/`
- [ ] NÃO commitar; NÃO tocar `Checkpoint.md`; NÃO tocar a semântica de troca de modelo em runtime (sprint 403)

---

## Guardrails anti-engodo (obrigatórios)

NÃO marcar concluída se:
- `apply_config_to_env` SOBRESCREVE env já presente (fura a precedência flag/CLI > config.toml — AC6 quebra).
- O parser <3.11 virou dependência externa (`tomli`) em vez de código stdlib vendorizado em `config_file.py`.
- `_handle_config_setup` continua fazendo `tmp.replace` do arquivo inteiro (ou qualquer escrita que apague chaves não citadas nas perguntas).
- O wizard ainda grava `model` (a chave que ninguém lê) em vez de `modelo`.
- Algum proof foi "provado" só com Python >=3.11 no AC3 (o contrato é ler SEM `tomllib`; o passo 4 força o caminho de linha).
- `settings.py` mudou a leitura de `extra_roots`/`ollama_port`/`proxy_port` de forma não byte-equivalente.
- `run.sh` passou a IGNORAR `NYX_MODEL` do ambiente (a precedência tem de ser env > toml > default).

Se algo falhar: `[SPRINT 436] BLOQUEADA: <motivo 1 linha>`.

---

## Proof-of-work esperado (comandos runtime-reais do BRIEF)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)
# implementar
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after.txt)
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

Baseline esperado: `FAIL_BEFORE = 0`, `FAIL_AFTER <= 0`. Colar: `inv_before`/`inv_after` (tail), `diff`, os outputs dos proofs (passos 3-6 dos Comandos de verificação), o `rg` do passo 2, `git --no-pager diff --stat` e `./run.sh --smoke` (deve imprimir `boot ok`).

Proofs runtime-reais do BRIEF aplicáveis SEM GPU: `./run.sh --smoke` (check #13), `bash scripts/sprint_invariants.sh` (14/14), `/home/andrefarias/.local/bin/ruff check ...`, `validar-acentuacao.py --paths ...`. Proof que exige GPU (serve real do modelo persistido end-to-end via proxy) fica **DEFERIDO para GPU exclusiva**.

---

## Gambiarras específicas desta sprint

- **Parser de linha <3.11:** o formato gravado pelo projeto é sempre `chave = valor` plano (sem tabelas TOML aninhadas `[grupo]`, sem arrays multi-linha exceto `extra_roots`). O parser mínimo cobre string com aspas, `true/false`, inteiro. Para `extra_roots` (lista), manter o caminho `tomllib` quando disponível e aceitar que em <3.11 `extra_roots` do toml fique vazio (env `NYX_EXTRA_ROOTS` segue funcionando) — documentar isso no docstring do parser, é degradação honesta, não silenciosa.
- **`apply_config_to_env` vs cache de tema:** `theme_manager` cacheia a paleta ativa; setar env em `load_settings` (cli.py:115, antes da 1a resolução de tema) evita cache frio com default. Se algum caminho resolver tema ANTES de `load_settings`, o executor deve mover a chamada para o ponto mais cedo do boot (documentar).
- **Booleano `auto_approve`:** o leitor é `nyx/cli_headless.py:58` que compara `== "1"`. Mapear `auto_approve = true` (toml) para `NYX_AUTO_APPROVE = "1"` (env) — não `"True"`.
- **run.sh sem parser Python:** ler `modelo` do toml no bash via `grep -oP '^modelo = "\K[^"]+'` (ou `sed`) é suficiente e evita subir o Python só para resolver o MODEL antes do proxy.

---

## Validação humana (checklist do usuário)

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git --no-pager show --stat HEAD

# Fluxo real de primeiro uso (com GPU exclusiva para o serve):
# 1. rm -f ~/.nyx/config.toml ~/.nyx/.first_run_done  (simular maquina nova)
# 2. ./run.sh --onboarding  (ou first-run) e escolher aesthetic/entity/schema/banner/modelo != default
# 3. sair e ./run.sh de novo: o banner/tema devem refletir as escolhas; o nome
#    escolhido deve aparecer no prompt (não "visitante"); o modelo servido deve ser
#    o escolhido. NADA volta ao default.
# 4. /config setup, ajustar tema, salvar; conferir que o NOME e a estetica do wizard
#    sobreviveram (cat ~/.nyx/config.toml).

ls dev-journey/06-sprints/concluidos/SPRINT_WIZARD_CONFIG_EFFECTIVE_01.md  # apos conclusao
```

---

## Riscos e não-objetivos

| Risco / não-objetivo | Decisão |
|-------|-----------|
| Troca de modelo em RUNTIME (comando/hot-swap durante a sessão) | **NÃO-OBJETIVO.** Coberto pela sprint 403 MODEL-SWAP-REAL-OR-HONEST-01. Esta sprint só trata a ADOÇÃO no BOOT do modelo persistido. Fronteira explícita para evitar sobreposição. |
| `extra_roots` (lista) em <3.11 | Degradação honesta: fica vazio pelo parser de linha; `NYX_EXTRA_ROOTS` (env) segue como fonte. Documentar no docstring. Se o dono quiser lista no toml em 3.10, abrir sprint própria (anti-débito, `feedback_nenhum_debito`). |
| Exigir Python 3.11+ no install (alternativa descartada) | Rejeitada: quebraria Ubuntu 22.04 sem deadsnakes — pior para a missão (público-alvo sem hardware/skill para PPA). O parser vendorizado resolve sem subir o piso. |
| Adicionar `tomli` ao requirements | Rejeitada: dependência externa nova num projeto local-first. Parser stdlib de ~15L cobre o formato plano do projeto. |
| `nyx/cockpit/server.py:633` propaga env de config (Onda 25/26) | Fora de escopo; não tocar. Com `apply_config_to_env` setando a env no boot, a propagação existente já herda os valores. |
| Migrar configs `config.toml` antigos com a chave `model` | Não-objetivo: essas chaves nunca funcionaram (ninguém as lia); um novo wizard regrava sob `modelo`. Sem migração necessária. |

---

## Fora de escopo (anti-débito)

As três faces do briefing são o MESMO mecanismo (schema de `config.toml` sem fonte única + leitor travado em 3.11 + escritores divergentes) e estão TODAS cobertas como ACs desta sprint (AC1-AC2 = Face 1; AC3 = Face 2; AC4 = Face 3; AC5 = braço bash da Face 1). Nada do briefing fica de fora. Itens adjacentes NÃO cobertos, para sprint própria se emergirem: (a) `extra_roots` como lista em <3.11; (b) troca de modelo em runtime (já é a sprint 403).

---

## Referências

- BRIEF: `/home/andrefarias/Desenvolvimento/Nyx-Code/VALIDATOR_BRIEF.md`
- Briefing da auditoria: `436_WIZARD-CONFIG-EFFECTIVE-01` (auditoria de prontidão 2026-07-12)
- Sprint relacionada (fronteira): `dev-journey/06-sprints/producao/SPRINT_MODEL_SWAP_REAL_OR_HONEST_01.md` (403 — troca em runtime)
- Precedente de estrutura + proof DEFERIDO GPU: `dev-journey/06-sprints/producao/SPRINT_EXEC_CONTRACT_PROXY_STATUS_BEFORE_JSON_01.md` (413)

---

*"Onboarding que promete e não cumpre é pior que onboarding nenhum: a primeira mentira ensina o usuário a não confiar na infra. Se a UI diz 'próximo boot já adota', o boot tem de adotar." — princípio de execução (ADR-032/033)*
