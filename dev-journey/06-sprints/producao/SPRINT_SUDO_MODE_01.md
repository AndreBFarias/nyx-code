# SPRINT SUDO-MODE-01 — Modo sudo com senha cacheada na sessão

## 0. SPEC

```yaml
sprint:
  id: SUDO-MODE-01
  title: "Modo sudo: agente pode rodar 'sudo X' em run_command; senha pedida 1x e cacheada na sessao"
  onda: 24
  bloco: 24.8 Escopo expandido
  prioridade: ALTA
  tipo: Feature
  dependencias: [AUDIT-01, INSTALL-SUDO-01, SHIFT-TAB-CYCLE-01]
  desbloqueia: [projetos que precisam apt-get/systemctl/instalar deps em runtime]
  origem: "Pedido do usuario 2026-05-18: 'o modo sudo que permite ele executar comandos sudo no terminal aí ele pede a senha sudo e passa a usar ela caso precise no projeto em diante'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/run_command.py
      reason: "Se mode==sudo, prefixar 'echo $NYX_SUDO_PASS_SESSION | sudo -S' antes do comando"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/sudo_mode.py
      reason: "Novo command /sudo enable/disable + handler para pedir senha"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Quando entra em sudo mode (shift+tab cycle), pergunta senha 1x"

  forbidden:
    - "Persistir senha em disco (~/.nyx/config.toml NUNCA armazena password)"
    - "Logar senha em stdout/stderr/arquivo (NUNCA)"
    - "Aceitar 'rm -rf /' ou comandos destruidores sem confirm extra"
    - "Reaproveitar NYX_SUDO_PASSWORD do install (escopo diferente)"

  tests:
    - cmd: "echo 'manual: shift+tab 2x para sudo mode, digite senha, peca para Nyx rodar sudo apt update'"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Ao entrar em sudo mode pela 1a vez, prompt pede senha (input mascarado via getpass)"
    - "Senha em memoria APENAS (variavel da sessao do REPL, nunca atinge disco/log)"
    - "run_command com mode=sudo prefixa 'echo $PASS | sudo -S'"
    - "Saida do sudo nao vaza senha (-S faz sudo ler de stdin sem ecoar)"
    - "Comandos destrutivos (rm -rf /, dd of=, mkfs) bloqueados mesmo em sudo mode"
    - "/sudo disable limpa cache + sai do modo"
    - "Ao sair do REPL, cache eh wiped (memset 0 se possivel)"
    - "Smoke + invariantes 14/14"
    - "AVISO de seguranca em README"
```

---

# Sprint SUDO-MODE-01

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Cenario: usuario pede ao Nyx instalar deps de um projeto que requer `apt install python3-dev`. Hoje run_command nao tem caminho de sudo (preflight bloqueia, ADR-009).

INSTALL-SUDO-01 ja resolveu sudo para `./install.sh` (via env var); esta sprint trata o caso **runtime**: agente roda `sudo X` durante REPL.

Modelo:
1. Usuario aperta shift+tab ate sudo mode (SHIFT-TAB-CYCLE-01).
2. Nyx prompta senha via getpass (chars mascarados).
3. Senha vai pra variavel da sessao (Python dict app_state, nao gravada).
4. Tools run_command + apt_install (futura) podem usar `echo $PASS | sudo -S`.
5. Sair do REPL (Ctrl+D) wipa a variavel.

## Solucao proposta

### nyx/agent/commands/sudo_mode.py

```python
@nyx_command(name="sudo", category="sistema",
             examples=["/sudo enable", "/sudo disable", "/sudo status"])
def cmd_sudo(args, root): ...
```

### nyx/cli.py keybinding (integrado com SHIFT-TAB-CYCLE-01)

Quando `mode` muda para "sudo":

```python
if old_mode != "sudo" and new_mode == "sudo":
    if not app_state.get("_sudo_pass"):
        import getpass
        try:
            pwd = getpass.getpass("  [sudo] senha: ")
            # Validar com sudo -v (testa sem rodar nada)
            if subprocess.run(
                ["sudo", "-S", "-v"], input=pwd + "\n",
                capture_output=True, text=True
            ).returncode == 0:
                app_state["_sudo_pass"] = pwd
                print(f"  {SUCCESS}● sudo cacheado{NC}")
            else:
                print(f"  {ERROR}senha invalida; sudo mode nao ativado{NC}")
                app_state["mode"] = "normal"
        except (KeyboardInterrupt, EOFError):
            print()
            app_state["mode"] = "normal"
```

### nyx/agent/tools/run_command.py

```python
def execute(args, app_state=None):
    cmd = args["cmd"]
    if app_state and app_state.get("mode") == "sudo":
        pwd = app_state.get("_sudo_pass")
        if pwd:
            # Lista negra de destruidores absolutos
            for danger in ("rm -rf /", "rm -rf ~", "dd of=/dev/", "mkfs"):
                if danger in cmd:
                    return error(f"comando destrutivo bloqueado mesmo em sudo: {danger}")
            # Wrap em sudo -S com password em stdin
            wrapped = f"sudo -S -p '' bash -c {shlex.quote(cmd)}"
            return _shell(wrapped, stdin=pwd + "\n")
    return _shell(cmd)
```

### Shutdown

```python
finally:
    if "_sudo_pass" in app_state:
        # Try memset to zeros (best-effort em Python)
        app_state["_sudo_pass"] = "0" * len(app_state["_sudo_pass"])
        del app_state["_sudo_pass"]
```

## Critério binário

- [ ] /sudo enable/disable/status
- [ ] getpass pede senha 1x
- [ ] Validar com `sudo -v` antes de cachear
- [ ] run_command em sudo mode prefixa corretamente
- [ ] Comandos destrutivos bloqueados mesmo com sudo
- [ ] Sudo cache wiped no shutdown
- [ ] README seção "Sudo mode" com AVISO de seguranca
- [ ] Audit grep zero hex/senha em logs
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(SUDO-MODE-01): modo sudo com senha cacheada na sessao`

---

## Riscos de seguranca explicitos

| Risco | Mitigacao |
|---|---|
| Senha vaza em log | Nunca printar; usar -S (stdin) |
| Senha em swap | Trade-off aceito; Linux/macOS swap eh privilegiado |
| Persistencia entre sessoes | NUNCA -- wipe no Ctrl+D |
| Comando destrutivo | Blacklist de patterns rm -rf /, dd of=, mkfs |
| Cache lift via dump de memoria | Risco aceito; mesmo nivel de sudo-cache do sistema |

---

*"Sudo na sessao, nao no disco." -- SUDO-MODE-01*
