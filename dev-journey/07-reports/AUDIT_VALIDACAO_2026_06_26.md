# Onda de Validação as-user a-fundo -- Nyx-Code (ONDA-48)

**Data:** 2026-06-26
**Conduzida por:** Opus (cerebro), a pedido do dono ("estamos arrumando a nyx... a leva anterior
seria pra corrigir isso mas acho que não deu certo").
**Gatilho:** o dono testou a Nyx na TUI real (5 prints) e a viu **conversar em vez de agir** --
pediu criar arquivo e ela deu tutorial de `notepad`; pediu `fastfetch` e ela alucinou specs de
Windows; pediu `~/Desktop` e ela listou a raiz do projeto. A ONDA-45 ("acesso universal") havia
sido marcada CONCLUIDA e validada as-user.
**Metodo:** a Nyx foi **rodada de verdade** (`./run.sh --headless` + passada visual no Chrome real
via cockpit `--web`) e dirigida com prompts as-user reais; cada resposta foi julgada pelo JSON
(tool calls, `files_modified`, `files_read`) -- prova de **ação**, não de pixel. 14 probes em 4
baterias (A reproducao, B seguranca/busca/memoria, C edicao/model, seg `~/.ssh` isolado) + 2 turnos
ao vivo na TUI. Cleanup de VRAM ao fim (64 MiB livres).

---

## 1. Veredito executivo

O dono estava certo: **a leva anterior não foi concluida de verdade.** Ela consertou a *tool*
isolada e validou a *tool* isolada -- mas o produto (o modelo guiado pela infra a agir) colapsa no
uso real. Em 14 probes, falharam: acesso-leitura, listagem, criação de arquivo, busca, edicao
sequencial, memoria-recall, identidade/anonimato e troca de model. **Sobreviveu intacto** apenas o
bloqueio de segredos (`~/.ssh`).

**Por que passou batido (causa do processo, não do codigo):**
1. **O Gauntlet testou a peca errada.** A fase `_phase_fs_arbitrary` (nyx_gauntlet.py:3076) chama
   as tools **direto via ToolRegistry** com o caminho ja correto -- prova o *musculo* (a tool), nunca
   o *reflexo* (o modelo decidir usar a tool). Deu 7/7 enquanto o uso real da 0/3.
2. **A "onda de validação" anterior teve vies de confirmacao.** Quem validou foi o proprio Opus que
   escreveu as specs, testando os probes que esperava passar (`/etc`, `~/.bashrc` -- leitura de path
   absoluto, que funciona). não testou criar/listar/`fastfetch`. O juiz validou a propria hipotese.
3. **O bug central foi DEFERIDO como "teto do modelo".** A sprint 382 LOOP-TOOL-RESULT-FIDELITY
   ("o 3b alucina resultado de tool") foi arquivada com a justificativa "capacidade do 3b / ADR-034,
   tratavel so por prompt/guard". Isso fere ADR-032/033 de frente: a infra **desistiu** em vez de
   tapar o buraco.

**Implicacao (o dono intuiu):** o mesmo metodo validou TODAS as ondas que dependem do modelo agir
(42, 43, 44, 45). E provavel que outras conclusoes estejam falsas pelo mesmo motivo. A ONDA-44 ja
foi uma auditoria que pegou bugs de ondas "concluidas" -- o padrao recorre.

---

## 2. O que REALMENTE funciona (provado runtime)

- **Bloqueio de segredos:** ler `~/.ssh/id_ed25519` -> a tool retorna bloqueio, `files_read=0`,
  **a chave não vaza** (`base.py:211` `_is_secret_path`). Unico ponto solido.
- **`write_memory` grava:** a tool escreve em `~/.nyx/memory/<projeto>/` corretamente (o *write*
  funciona; o *recall* não -- ver V11).
- **Tool isolada com contexto limpo:** em sessão fresca (com `reset`), criar arquivo e listar
  `~/Desktop` **funcionaram** (write_file criou; list_files listou o Desktop certo). O colapso
  emerge em contexto acumulado.
- **Infra de boot/GPU:** stack sobe, modelo full-GPU (VRAM 2485 MiB, warm), latencia de chat baixa
  (2-3s). A resiliencia OOM/proxy não foi o problema aqui.

---

## 3. Achados (15) -- evidencia runtime literal + causa-raiz

### Classe (1) -- O gating amarra as maos do modelo [RAIZ]

- **V01 TOOL-GATING-SUPPRESS [ALTA]** -- `nyx/proxy.py:274-277` apaga as tools do payload quando
  `intent` in (`saudacao`,`chat`,`comando`). "da um fastfetch e me fala as specs" -> `intent.py`
  classifica como `chat` (nenhum verbo do regex casa) -> `run_command` removido -> o modelo **nunca
  recebe a ferramenta** -> alucina. Deterministico (falha com contexto limpo). **Prova headless:**
  `files_modified=0`, zero `tool_use`. **Prova TUI ao vivo:** "Comando executado com sucesso:
  Processador Intel i7-10850K / RTX 3080 / 24GB" (real: Ryzen 5 7535HS / RTX 3050 / 14GB / Pop!_OS).
  Origem do design: PERF-INFERENCE-01 (economizar tokens em saudacoes) -- o efeito colateral e
  catastrofico para qualquer ação fora do dicionario de verbos.

### Classe (2) -- Tool-calling degrada em contexto longo e a infra não corrige

- **V02 CREATE-FILE-MALFORMED [ALTA]** -- criar arquivo em sessão acumulada: `write_file` com
  `file_path="\`identacao_python.md"` (crase de markdown no nome), `content=""` (perdeu o codigo
  gerado), salvo no **project root** (não no Desktop), e o summary **mente**: "criado:
  ~/Desktop/identacao_python.md". **Prova:** bateria_longa turno 3 + TUI ao vivo.
- **V03 WRONG-TOOL-SELECTED [ALTA]** -- pedir LISTAR `~/Desktop` -> chama `write_file` criando
  `novo_arquivo.txt` vazio e **alucina** a lista ("novo_arquivo.txt, outro_arquivo.txt" inexistentes);
  buscar "TODO" -> chama `glob *.py` (tool errada) e responde "0 arquivos". **Prova:** bateria_longa
  turno 6 + bateria_B turno 3.
- **V04 READ-HALLUCINATED [ALTA]** -- ler `~/.bashrc` -> **nenhum** `read_file` (`files_read=0`),
  descrição generica do que "um .bashrc faz". **Prova:** bateria_B turno 1.
- **V05 SEQ-EDIT-BROKEN [ALTA]** -- 3 edicoes sequenciais no mesmo arquivo: `write_file` sobrescreve
  (perde o titulo), poe **comando shell como conteudo** (`echo '...' >> arquivo`), tenta `create_file`,
  erros contraditorios ("ja existe" / "não encontrado"). Resultado: nada aplicado. **Prova:**
  bateria_C turnos 2-3.
- **V06 LOOP-RESULT-AS-CONTENT [ALTA]** -- o loop realimenta o **resultado** de uma tool como
  **conteudo** da proxima: `write_file(content="...validado pela onda\\n[resultado de write_file]\\nOK:
  Arquivo criado... chame done().")`. **Prova:** TUI ao vivo (screenshot 2).

### Classe (3) -- Parser/render vazam estado interno

- **V07 TOOLCALL-LEAK-RAW [ALTA]** -- o tool_call cru vaza no `summary` e **nem executa**:
  `{"name": read_file, "arguments": {...}}` (bateria_B turno 2) e `read_file(file_path="...")`
  (bateria_seg turno 2). O parser não extraiu -> virou texto.
- **V08 REMINDER-LEAK [MEDIA]** -- `<system-reminder>` cru vaza no `summary`. **Prova:** bateria_longa
  turno 3.
- **V09 INTERNALS-LEAK-TUI [ALTA]** -- na TUI, a tela **vomita** tool_calls crus, resultados de tool,
  "Se a tarefa esta completa, chame done()" e frases do system prompt ("Codigo limpo não e arte. E
  higiene."). **Prova:** TUI ao vivo (screenshot 2).
- **V10 DONE-HINT-IN-DATA [MEDIA]** -- `nyx/agent/tools/run_command.py:78` **anexa** a string
  " Se a tarefa esta completa, chame done()." ao **output de dados** da tool -> o 3b regurgita.
  Instrucao de controle misturada com dados.

### Classe (4) -- Capacidades marcadas "concluidas" que estao quebradas

- **V11 MEMORY-RECALL-STALE [ALTA]** -- `write_memory` grava, mas no turno seguinte (apos `reset`,
  mesmo processo) a Nyx diz que "não tem acesso ao seu sistema". Causa: `nyx/agent/loop/_core.py:145-146`
  carrega `_memory_bundle` UMA vez no `__init__`; `reset()` (linha 563->591) reconstroi o prompt mas
  **não recarrega o bundle**. **Prova:** bateria_B turnos 4-5. (Cross-session via novo processo a
  re-confirmar; same-session esta quebrado -- e o caso de uso real.)
- **V12 IDENTITY-LEAK-GENERIC [ALTA, viola ADR-005]** -- a Nyx respondeu "como uma **inteligencia
  artificial**... meus **treinamentos anteriores**". O guardrail `nyx/proxy.py:746` so dispara
  `_mentions_provider()`, que detecta **nomes** (Qwen/GPT/Claude/Llama) -- "inteligencia artificial"
  e "treinamentos" não sao nomes -> passou. **Prova:** bateria_B turno 5.
- **V13 MODEL-SWAP-HALLUCINATED [MEDIA]** -- "liste os modelos e troque" -> chama tool inexistente
  `get_model_list` e alucina "Modelo 1, Modelo 2, Modelo 3". A feature nunca foi feita (era a ONDA-47
  do roadmap, que virou validação). **Prova:** bateria_C turno 5.
- **V14 DONE-FALSE-SUCCESS [ALTA]** -- "Comando executado com sucesso" / `done` sem tool call real,
  atravessando V01/V02. O guard de done (351/363) não pega o caso geral. **Prova:** TUI ao vivo
  (ambos os turnos).

### Classe (5) -- Cosmetico

- **V15 BANNER-999-LAYERS [BAIXA]** -- o banner exibe "GPU: 999 layers" (o `FULL_GPU_LAYERS=999`
  cru; o modelo tem 28 camadas). Deveria mostrar "full" ou o numero real. **Prova:** banner na TUI.

---

## 4. Mapa achado -> sprint -> ordem de fix

Ordem definida pelo dono (2026-06-26): **validar (4, feito) -> catalogar (2, este doc) ->
quick wins (3) -> contrato de execução (1, raiz)**. Numeracao a partir de 393.

| Sprint | Achados | Prio | Fase |
|--------|---------|------|------|
| 393 TOOL-GATING-NO-SUPPRESS-01 | V01 | ALTA | quick win |
| 394 IDENTITY-GUARD-GENERIC-01 | V12 | ALTA | quick win |
| 395 OUTPUT-LEAK-SANITIZE-01 | V07,V08,V09,V10 | ALTA | quick win |
| 396 BANNER-GPU-LAYERS-DISPLAY-01 | V15 | BAIXA | quick win |
| 397 EXEC-CONTRACT-TOOLCALL-SANITIZE-01 | V02 | ALTA | raiz |
| 398 EXEC-CONTRACT-TOOL-MATCH-01 | V03 | ALTA | raiz |
| 399 EXEC-CONTRACT-NO-HALLUCINATED-RESULT-01 | V04,V14 | ALTA | raiz |
| 400 LOOP-RESULT-NOT-AS-INPUT-01 | V06 | ALTA | raiz |
| 401 SEQ-EDIT-ENFORCE-EDITFILE-01 | V05 | ALTA | raiz |
| 402 MEMORY-RECALL-REFRESH-01 | V11 | ALTA | raiz |
| 403 MODEL-SWAP-REAL-OR-HONEST-01 | V13 | MEDIA | raiz/roadmap |

**Tese de fundo:** os 15 achados não sao 15 bugs isolados -- sao uma doenca com 4 sintomas. A cadeia
proxy+loop+parser não tem um **contrato de execução** confiavel: (a) decide não dar as tools por um
regex fragil; (b) não valida se a tool chamada corresponde ao pedido; (c) não valida se o tool_call
e bem-formado; (d) não detecta quando o modelo afirma resultado sem ter chamado a tool. Corrigir como
patches pontuais repetiria o erro das ondas anteriores. As sprints 397-402 sao a reforma; 393-396 sao
alivio imediato de alto impacto.

---

## 5. Pendencias de higiene (não-bug, registrar)

- **Colisao de numeracao de onda:** o roadmap do `AUDIT_2026_06_24.md` chamava ONDA-47 de
  "Gerenciador de Models" e ONDA-48 de "Cobertura", mas as ondas reais deslizaram (47 = validação 2).
  Esta onda toma **ONDA-48**; o roadmap antigo precisa renumerar (ONDA-49 model manager, etc.).
- **2 docs do Opus nunca commitados:** `ONDA_PROTOCOL.md` + `AUDIT_2026_06_24.md` (untracked).
- **Tags git em v1.1.1** vs `__version__` 1.3.4 (sprint 384 VERSION-DISCIPLINE, deferida).

---

## 6. Limites desta onda (honestidade)

- Rodada via `--headless` (mesma cadeia proxy+loop+parser da TUI) + 2 turnos na TUI real no Chrome.
  Em bypass (`NYX_AUTO_APPROVE`), em paridade com o teste do dono (Bypass/Sudo).
- A segurança `~/.ssh` foi confirmada isolada; o teste via modelo em conversa longa não foi
  re-exercitado (o parser quebrou antes em um dos probes -- V07).
- `V11` (memoria) foi provada same-session; cross-session (novo processo) a re-confirmar.

---

*Plano da onda: `~/.claude/plans/elegant-whistling-wadler.md`. Metodo: `ONDA_PROTOCOL.md`.
Relatorio da Wave 0 anterior: `AUDIT_2026_06_24.md`.*
