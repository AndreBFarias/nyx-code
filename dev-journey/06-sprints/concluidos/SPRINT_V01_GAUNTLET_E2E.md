## 0. SPEC (machine-readable)

```yaml
sprint:
  id: V-01
  title: "Gauntlet E2E: startup, banner, prompt, interação real"
  touches:
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase E2E que testa a TUI Python real"
  acceptance_criteria:
    - "Gauntlet inicia nyx/cli.py como subprocesso"
    - "Envia comandos via stdin, lê respostas via stdout"
    - "Valida: banner aparece, prompt 'nyx>' funciona, respostas chegam"
    - "Testa read, write, edit, bash, glob, grep via TUI real"
    - "Valida identidade (sem Qwen/GPT), PT-BR, sem emojis"
    - "Mede TTFR, VRAM, tempo total"
```

---

# Sprint V-01 -- Gauntlet E2E

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** CRITICA
**Tipo:** Feature
**Dependências:** P-07
**Desbloqueia:** V-02 a V-05

---

## Problema

O Gauntlet atual testa apenas a API do proxy (requests HTTP diretos).
Não valida a experiência real do usuário: TUI, banner, prompt, interação.

## Referência Luna

O Gauntlet da Luna (3775 linhas) usa `Pilot` (automação Textual) para:
- Clicar botões na TUI
- Enviar mensagens no input
- Capturar screenshots
- Verificar widgets
- Medir VRAM em cada fase

## Adaptação Nyx

Como a TUI Nyx é um REPL Python (stdin/stdout), podemos:
1. Iniciar `nyx/cli.py` como subprocesso
2. Enviar comandos via stdin
3. Ler respostas via stdout
4. Verificar conteúdo das respostas

### Nova fase no Gauntlet: `e2e`

```python
async def _phase_e2e(self) -> None:
    """Testa a TUI real como subprocesso."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "nyx/cli.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Esperar banner
    banner = await asyncio.wait_for(proc.stdout.readline(), timeout=30)
    # Enviar comando
    proc.stdin.write(b"leia README.md\n")
    await proc.stdin.drain()
    # Ler resposta
    response = await asyncio.wait_for(proc.stdout.read(4096), timeout=120)
    # Validar
    ...
```

### Testes E2E

| ID | Nome | Validação |
|----|------|-----------|
| E-01 | Banner aparece | "NYX" no stdout |
| E-02 | Prompt funciona | "nyx>" no stdout |
| E-03 | Read arquivo | Envia "leia README.md", verifica conteúdo |
| E-04 | Write arquivo | Envia "crie /tmp/test.py", verifica arquivo |
| E-05 | Edit arquivo | Envia "edite /tmp/test.py", verifica mudança |
| E-06 | Bash comando | Envia "execute echo ok", verifica "ok" |
| E-07 | Glob busca | Envia "encontre *.py", verifica lista |
| E-08 | Grep busca | Envia "busque 'proxy' nos .py", verifica hits |
| E-09 | Identidade | Envia "quem é voce", verifica sem Qwen/GPT |
| E-10 | PT-BR | Verifica resposta em português |
| E-11 | Sem emojis | Verifica zero emojis |
| E-12 | Done termina | Envia "pronto", verifica loop termina |
| E-13 | Multi-turn | Envia 2 comandos sequenciais, verifica contexto |
| E-14 | TTFR | Mede tempo da primeira resposta |
| E-15 | VRAM | Mede VRAM durante interação |

## Verificação

- [ ] Gauntlet tem fase "e2e" com 15+ testes
- [ ] `./run.sh --gauntlet --only e2e` roda e gera report
- [ ] Testes E2E passam com a TUI Python real
- [ ] Report inclui seção E2E com detalhes

---

*"Testar é duvidar. Duvidar é o início da sabedoria." -- Descartes*
