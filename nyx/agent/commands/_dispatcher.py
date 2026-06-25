"""Dispatcher de slash commands -- roteia input do REPL para o handler.

ERROR-MSG-01: comando desconhecido devolve string sentinela
``__error__<linha pronta>`` para o cli.py imprimir via print_error,
com sugestão de comando próximo via difflib.get_close_matches
(cutoff 0.6, n=1). Argumentos válidos passam sem alteração.
"""

from __future__ import annotations

from difflib import get_close_matches

from nyx.agent.commands._registry import _COMMANDS, get_command

ERROR_SENTINEL = "__error__"

# INPUT-SLASH-PATH-DISAMBIG-01: resultados da disambiguação de entrada com `/`.
SLASH_COMMAND = "command"  # 1o token casa comando registrado -> executa
SLASH_CHAT = "chat"        # caminho absoluto ou frase -> vai pro LLM (barra intacta)
SLASH_UNKNOWN = "unknown"  # token único sem cara de caminho -> aviso desconhecido


def classify_slash_input(text: str) -> str:
    """Decide o destino de uma entrada que começa com `/` (fonte única REPL+TUI).

    INPUT-SLASH-PATH-DISAMBIG-01: o gating histórico `startswith('/')` tratava
    qualquer entrada iniciada por barra como slash-command, fazendo caminhos
    absolutos (`/home/...`) e frases virarem 'Comando desconhecido'. Esta função
    é a fonte de verdade compartilhada entre cli.py (REPL), tui/app.py (TUI) e
    cli_headless.py, evitando divergência de comportamento.

    Regras (na ordem):
      1. 1o token (sem a barra, minúsculo) casa um comando registrado
         -> SLASH_COMMAND (executa; cobre /help, /commit, /cd e aliases).
      2. senão, parece caminho absoluto (barra interna no 1o token, ex.:
         `/home/x` ou `/etc/hostname`) OU tem espaço (frase) -> SLASH_CHAT
         (envia ao LLM com a barra preservada no texto).
      3. senão (token único, sem barra interna, cara de comando) -> SLASH_UNKNOWN
         (mantém o aviso 'Comando desconhecido' + dica /help).

    Retorna SLASH_COMMAND para entrada que não começa com `/` (defensivo: o
    callsite já filtrou via startswith, então trata como antes).
    """
    if not text.startswith("/"):
        return SLASH_COMMAND

    body = text[1:]
    # 1o token = parte antes do 1o espaço; preserva barras internas pra heurística.
    pieces = body.split(maxsplit=1)
    first = pieces[0] if pieces else ""
    if get_command(first.lower()):
        return SLASH_COMMAND

    has_space = len(pieces) > 1          # frase (há texto depois do 1o token)
    looks_like_path = "/" in first       # caminho absoluto /algo/... (barra interna)

    if looks_like_path or has_space:
        return SLASH_CHAT

    return SLASH_UNKNOWN


def _format_unknown_command(name: str) -> str:
    """Monta a mensagem sentinela para comando desconhecido.

    Formato: ``__error__<msg>||<hint>`` -- o dispatcher no cli.py
    decompõe em ``msg`` e ``hint`` para passar ao print_error.
    Se houver sugestão próxima (score >= 0.6), o hint vira
    ``Você quis dizer /<sug>?``, caso contrário ``Use /help para
    listar comandos disponíveis.``
    """
    names = sorted({cmd.name for cmd in _COMMANDS.values()})
    sugestoes = get_close_matches(name, names, n=1, cutoff=0.6)
    if sugestoes:
        hint = f"Você quis dizer /{sugestoes[0]}?"
    else:
        hint = "Use /help para listar comandos disponíveis."
    return f"{ERROR_SENTINEL}Comando desconhecido: /{name}.||{hint}"


def handle_command(cmd_input: str, project_root: str = ".") -> str | None:
    """Processa um slash command. Retorna None se não é comando."""
    if not cmd_input.startswith("/"):
        return None

    parts = cmd_input[1:].split(" ", 1)
    name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    cmd = get_command(name)
    if not cmd:
        return _format_unknown_command(name)

    return cmd.handler(args, project_root)


# "O roteamento certo resolve metade dos problemas." -- adágio de engenharia
