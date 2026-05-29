"""Comando /plan -- checklist persistida opt-in (CTX-04 / GSD-B).

Subcomandos:
  /plan <objetivo>       cria/redefine objetivo (preserva itens se já existe)
  /plan add <texto>      adiciona item à checklist
  /plan done <n>         marca item n (1-based) como concluído
  /plan show             imprime checklist renderizada
  /plan clear            apaga objetivo + itens + arquivo em disco

Plan é opt-in. Não há criação automática -- só vira ativo quando o dev
roda /plan explicitamente. Vive em ~/.nyx/active_plan.md (singleton
por usuário, persiste entre sessões).
"""

from __future__ import annotations

from nyx.agent.active_plan import ActivePlan
from nyx.agent.commands._registry import nyx_command

_USAGE = (
    "  Uso: /plan <subcomando>\n"
    "    <objetivo>     define objetivo (cria plan se ausente)\n"
    "    add <texto>    adiciona item à checklist\n"
    "    done <n>       marca item n como concluído (1-based)\n"
    "    show           imprime checklist renderizada\n"
    "    clear          apaga plan ativo"
)


@nyx_command(
    name="plan",
    description="Checklist persistida do plano ativo (opt-in)",
    category="sessão",
    examples=[
        "/plan portar streaming do TS para Python",
        "/plan add ler nyx/agent/streaming.py",
        "/plan done 1",
    ],
)
def cmd_plan(args: str, _root: str) -> str:
    args = args.strip()
    if not args:
        return _USAGE

    parts = args.split(" ", 1)
    head = parts[0].lower()
    tail = parts[1].strip() if len(parts) > 1 else ""

    plan = ActivePlan.get()

    if head == "show":
        body = plan.render()
        if not body:
            return (
                "  Nenhum plano ativo. Use /plan <objetivo> para começar."
            )
        return "\n" + body + "\n"

    if head == "clear":
        if plan.is_empty():
            return "  Nenhum plano ativo para limpar."
        plan.clear()
        ActivePlan.reset_singleton()
        return "  Plano ativo removido."

    if head == "add":
        if not tail:
            return (
                "__error__/plan add precisa de texto."
                "||Uso: /plan add <texto do item>"
            )
        try:
            idx = plan.add(tail)
        except ValueError:
            return (
                "__error__Item vazio em /plan add."
                "||Forneça texto não vazio."
            )
        return f"  Item {idx} adicionado: {tail}"

    if head == "done":
        if not tail:
            return (
                "__error__/plan done precisa de um número."
                "||Uso: /plan done <n> (n = índice 1-based do item)"
            )
        try:
            n = int(tail.split()[0])
        except ValueError:
            return (
                f"__error__Argumento inválido em /plan done: '{tail}'."
                "||Esperado: inteiro positivo (ex: /plan done 2)."
            )
        if not plan.done(n):
            total = len(plan.items)
            return (
                f"__error__Índice {n} fora do intervalo (1..{total})."
                "||Use /plan show para ver a checklist."
            )
        return f"  Item {n} marcado como concluído."

    # Sem subcomando reconhecido: tratar args inteiros como objetivo.
    plan.objective = args
    plan.save(plan.path)
    return f"  Objetivo do plano definido: {args}"


# "Quem mede o caminho não se perde no escuro." -- ditado popular
