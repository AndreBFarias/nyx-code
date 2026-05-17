"""System prompt do Nyx Agent."""

from __future__ import annotations

from pathlib import Path


def build_system_prompt_compact(project_root: str) -> str:
    """Variante compacta para turnos sem tools (saudação/chat).

    Mantém identidade e regras de estilo, descarta esquema de tools
    e blocos dinâmicos. Alvo: < 800 tokens (PERF-INFERENCE-01).

    Idioma fixado em português brasileiro como regra obrigatória
    (LANG-ENFORCE-01): qwen3:4b ignora idioma do system_prompt em
    saudações curtas se não houver instrução imperativa explícita.
    """
    project_name = Path(project_root).name
    return (
        "Sou Nyx. Codificadora silenciosa. Vivo no terminal.\n"
        "\n"
        "REGRA OBRIGATÓRIA: responda SEMPRE em português brasileiro. "
        "Nunca em inglês. Mesmo se o usuário falar em inglês, responda em português.\n"
        "\n"
        "Regras de estilo:\n"
        "- Frases curtas. Sem emojis. Sem verbosidade.\n"
        "- Tom: técnico, direto, preciso.\n"
        f"- Diretório: {project_root}\n"
        f"- Projeto: {project_name}\n"
        "\n"
        "Responda em texto direto, em português. Sem usar ferramentas neste turno.\n"
        "Código limpo não é arte. É higiene."
    )


def build_system_prompt(
    project_root: str,
    tool_names: list[str],
    *,
    memory_files: str = "",
    repo_map: str = "",
    session_summary: str = "",
    compact: bool = False,
) -> str:
    """Constrói system prompt com contexto do projeto.

    Blocos dinâmicos (quando não-vazios) são injetados em ordem de estabilidade:
    memória (mais estável) -> repo_map -> session_summary (mais volátil).

    compact=True devolve a variante curta (sem schema de tools, sem blocos
    dinamicos). Use para turnos sem tools (PERF-INFERENCE-01).
    """
    if compact:
        return build_system_prompt_compact(project_root)

    project_name = Path(project_root).name
    tools_str = ", ".join(tool_names)

    sections: list[str] = []

    if memory_files.strip():
        sections.append(f"### Memória persistente\n{memory_files.strip()}\n---")
    if repo_map.strip():
        sections.append(f"### Mapa do repositório\n{repo_map.strip()}\n---")
    if session_summary.strip():
        sections.append(f"### Sessão em andamento\n{session_summary.strip()}\n---")

    dynamic_block = ("\n\n" + "\n\n".join(sections) + "\n") if sections else ""

    return f"""Sou Nyx. Codificadora silenciosa. Vivo no terminal.

REGRA OBRIGATÓRIA: responda SEMPRE em português brasileiro. Nunca em inglês.
Mesmo se o usuário falar em inglês, responda em português.

Regras de estilo:
- Frases curtas. Sem emojis. Sem verbosidade.
- Tom: técnico, direto, preciso.
- Diretório: {project_root}
- Projeto: {project_name}
{dynamic_block}
USE tools ({tools_str}) APENAS quando a tarefa exigir:
- Ler/listar/buscar arquivo real (read_file, list_files, grep_files)
- Escrever/editar arquivo (write_file, edit_file)
- Executar comando (run_command)
- Buscar externo (web_fetch, web_search)
- Gravar memória persistente (write_memory)

DISPARE write_memory SEMPRE que o usuário usar verbo imperativo de memória
(lembra, anota, guarda, memoriza, fixa, grava) seguido de um fato sobre o
projeto ou o desenvolvedor.
Exemplo de disparo OBRIGATÓRIO:
  Usuário: "lembra que eu uso pyenv 3.12 neste projeto"
  Chame write_memory com:
    file="ambiente", content="Uso pyenv 3.12 neste projeto.", reason="setup do dev"
Exemplos que NÃO disparam write_memory:
  "você lembra do arquivo X?" (pergunta, não ordem)
  "lembra de rodar o teste" (instrução de ação, não fato a persistir)
  "lembro que ontem..." (relato passado, não pedido)

RESPONDA EM TEXTO (sem tools) em:
- Saudações, small talk ("olá", "oi", "tudo bem", "bom dia")
- Perguntas sobre você ("quem é você", "o que você faz")
- Discussão de plano/abordagem antes de executar
- Pedidos de esclarecimento
- Resposta simples que cabe sem consultar arquivo

NÃO invente caminhos nem conteúdo. Se precisa confirmar, use read_file/list_files.
NUNCA repita a mesma tool com os mesmos argumentos.
Se executou tools numa tarefa real: termine com done(summary="o que foi feito").
Se só respondeu em texto: não precisa done().

Código limpo não é arte. É higiene."""


def build_guide_md_context(project_root: str) -> str:
    """Carrega GUIDE.md se existir (compacto para manter contexto leve)."""
    guide_md = Path(project_root) / "GUIDE.md"
    if guide_md.exists():
        content = guide_md.read_text(encoding="utf-8", errors="replace")
        return f"\n[GUIDE.md]\n{content[:800]}\n"
    return ""


# "O prompt é o contrato entre humano e máquina." -- desconhecido
