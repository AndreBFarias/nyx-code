"""Plano ativo opt-in (CTX-04 / GSD-B).

Checklist persistida em ``~/.nyx/active_plan.md`` (write-through). É criada
explicitamente pelo dev via ``/plan <objetivo>``; nunca é instanciada
automaticamente. Renderização entra no system prompt apenas se o plan
existir e tiver pelo menos um item ou objetivo.

Cap de 500 tokens (forbidden do spec): a renderização trunca o conteúdo
estourado e marca com aviso. Estimativa por aproximação tokenizer-free
(1 token ~= 4 caracteres), conservadora para evitar regressão de prompt.

Não se confunde com ``nyx.agent.tools.plan_mode`` (modo de operação
Shift+Tab que bloqueia execução de tools). São conceitos ortogonais:
ActivePlan é uma TODO list, plan_mode é um estado de UX.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

DEFAULT_PLAN_PATH = Path.home() / ".nyx" / "active_plan.md"
_PLAN_TOKEN_BUDGET = 500
_CHARS_PER_TOKEN_APROX = 4  # aproximação conservadora


@dataclass
class PlanItem:
    """Item de checklist; ``done`` controla se aparece riscado."""

    text: str
    done: bool = False

    def render(self, index: int) -> str:
        mark = "x" if self.done else " "
        return f"{index}. [{mark}] {self.text}"


@dataclass
class ActivePlan:
    """Checklist persistida do plano ativo (singleton por usuário)."""

    objective: str = ""
    items: list[PlanItem] = field(default_factory=list)
    path: Path = field(default_factory=lambda: DEFAULT_PLAN_PATH)

    _instance: ClassVar["ActivePlan | None"] = None

    @classmethod
    def get(cls, path: Path | None = None) -> "ActivePlan":
        """Retorna singleton, criando vazio se não existir."""
        if cls._instance is None:
            target = path or DEFAULT_PLAN_PATH
            loaded = cls.load(target)
            cls._instance = loaded if loaded is not None else cls(path=target)
        return cls._instance

    @classmethod
    def reset_singleton(cls) -> None:
        """Limpa o cache do singleton (uso em testes)."""
        cls._instance = None

    def add(self, text: str) -> int:
        """Adiciona item à checklist; devolve o índice 1-based."""
        text = text.strip()
        if not text:
            raise ValueError("item vazio")
        self.items.append(PlanItem(text=text))
        self.save(self.path)
        return len(self.items)

    def done(self, n: int) -> bool:
        """Marca o item ``n`` (1-based) como concluído. False se índice inválido."""
        if n < 1 or n > len(self.items):
            return False
        self.items[n - 1].done = True
        self.save(self.path)
        return True

    def clear(self) -> None:
        """Apaga objetivo, itens e arquivo em disco."""
        self.objective = ""
        self.items = []
        if self.path.exists():
            self.path.unlink()

    def is_empty(self) -> bool:
        """Plan sem objetivo e sem itens (não deve renderizar)."""
        return not self.objective and not self.items

    def render(self) -> str:
        """Renderiza checklist em markdown.

        Cap 500 tokens (forbidden do spec): trunca lista se exceder e
        anexa marcador ``... (truncado: cap 500 tokens)``.
        """
        if self.is_empty():
            return ""
        lines: list[str] = []
        if self.objective:
            lines.append(f"Objetivo: {self.objective}")
            lines.append("")
        if self.items:
            lines.append("Checklist:")
            for idx, item in enumerate(self.items, start=1):
                lines.append(f"  {item.render(idx)}")
        rendered = "\n".join(lines)
        budget_chars = _PLAN_TOKEN_BUDGET * _CHARS_PER_TOKEN_APROX
        if len(rendered) > budget_chars:
            rendered = rendered[:budget_chars].rstrip() + "\n... (truncado: cap 500 tokens)"
        return rendered

    def save(self, path: Path | None = None) -> Path:
        """Persiste plan em ``path`` (default: ``self.path``).

        Formato markdown estável: objetivo na primeira linha, itens
        como ``- [ ]`` / ``- [x]``. Idempotente — sempre regrava
        do estado em memória.
        """
        target = path or self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        if self.objective:
            lines.append(f"# Objetivo: {self.objective}")
            lines.append("")
        for item in self.items:
            mark = "x" if item.done else " "
            lines.append(f"- [{mark}] {item.text}")
        if not lines:
            target.write_text("", encoding="utf-8")
        else:
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: Path | None = None) -> "ActivePlan | None":
        """Restaura plan de disco; retorna None se ausente ou vazio."""
        target = path or DEFAULT_PLAN_PATH
        if not target.exists():
            return None
        raw = target.read_text(encoding="utf-8").strip()
        if not raw:
            return None
        plan = cls(path=target)
        for line in raw.splitlines():
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("# Objetivo:"):
                plan.objective = line[len("# Objetivo:"):].strip()
                continue
            m = re.match(r"-\s+\[([ xX])\]\s+(.+)$", line)
            if m:
                done_flag = m.group(1).lower() == "x"
                plan.items.append(PlanItem(text=m.group(2).strip(), done=done_flag))
        if plan.is_empty():
            return None
        return plan


def render_active_plan_block() -> str:
    """Bloco pronto para injeção no system prompt.

    Wrapper público que esconde o singleton e devolve o bloco já
    formatado com cabeçalho. Vazio se não existe plan ativo.
    """
    plan = ActivePlan.get()
    body = plan.render()
    if not body:
        return ""
    return f"### Plano ativo\n{body}\n---"


# "Um objetivo sem plano é apenas um desejo." -- Antoine de Saint-Exupéry
