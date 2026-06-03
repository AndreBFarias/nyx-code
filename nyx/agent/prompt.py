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
    active_plan: str = "",
    compact: bool = False,
    output_style: str = "default",
) -> str:
    """Constrói system prompt com contexto do projeto.

    Blocos dinâmicos (quando não-vazios) são injetados em ordem de estabilidade:
    memória (mais estável) -> repo_map -> session_summary -> active_plan
    (mais volátil; CTX-04).

    compact=True devolve a variante curta (sem schema de tools, sem blocos
    dinamicos). Use para turnos sem tools (PERF-INFERENCE-01).

    output_style (OUTPUT-STYLES-01): "default" | "concise" | "learning";
    injeta hint_prompt no bloco final. ADRs invariantes em todos os estilos.

    active_plan (CTX-04): bloco já formatado vindo de
    ``ActivePlan.render()``. Caller é responsável pelo cap de 500 tokens.
    Se vazio, bloco não aparece.
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
    if active_plan.strip():
        sections.append(active_plan.strip())

    dynamic_block = ("\n\n" + "\n\n".join(sections) + "\n") if sections else ""

    # OUTPUT-STYLES-01: hint do estilo entra na cauda do prompt.
    style_block = ""
    if output_style and output_style != "default":
        from nyx.agent.output_style import get_style

        style = get_style(output_style)
        if style.hint_prompt:
            style_block = (
                f"\n\nEstilo de saída ativo ({style.name}): "
                f"{style.hint_prompt}\n"
            )

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
NUNCA afirme "criado/salvo/escrito/gerado/gravado com sucesso" se não usou
write_file, edit_file, create_file, multi_edit ou patch no turno corrente.
Se o usuário pediu ação mas o preflight/permissão bloqueou, explique o motivo
real do bloqueio sem inventar execução.
Se executou tools numa tarefa real: termine com done(summary="o que foi feito").
Se só respondeu em texto: não precisa done().

Código limpo não é arte. É higiene.{style_block}"""


def build_guide_md_context(project_root: str) -> str:
    """Carrega GUIDE.md se existir (compacto para manter contexto leve)."""
    guide_md = Path(project_root) / "GUIDE.md"
    if guide_md.exists():
        content = guide_md.read_text(encoding="utf-8", errors="replace")
        return f"\n[GUIDE.md]\n{content[:800]}\n"
    return ""


def build_reminder(
    session,
    project_root: str,
    original_input: str | None = None,
    extra: str | None = None,
) -> str:
    """Bloco <system-reminder> com estado canônico do turno.

    NYX-PROMPT-REINJECT-01: reinjetado periodicamente no histórico para
    contrariar drift de modelos pequenos (qwen2.5-coder:3b) em tarefas
    multi-turno. Padrão: bloco <system-reminder> reaparece entre tool
    results para reafirmar pedido original, estado e invariantes.

    - session: CodeSession (lê iteration, files_read_count, files_modified_count).
    - project_root: caminho absoluto do sandbox vigente.
    - original_input: pedido original do usuário do turno atual.
    - extra: linha opcional anexada antes de </system-reminder> (drift hints).
    """
    meta = (original_input or "(pedido não registrado)").replace("\n", " ")[:200]
    iter_n = getattr(session, "iteration", 0)
    lidos = getattr(session, "files_read_count", 0)
    modif = getattr(session, "files_modified_count", 0)
    lines = [
        "<system-reminder>",
        f"Pedido original: {meta}",
        f"Estado: iter={iter_n}, lidos={lidos}, modif={modif}",
        "Invariantes vigentes (lembrar SEMPRE):",
        "- Você é Nyx-Code. Sem menção a IA externa.",
        "- Responda em PT-BR acentuado.",
        "- Sem emoji em código/output user-facing.",
        "- Use tools (write_file/edit_file/run_command) -- NUNCA afirme sucesso sem tool call real.",
        f"- Sandbox: pode tocar apenas {project_root} (e roots extra opt-in).",
        # LOOP-PRESENT-TOOL-RESULT-01 (#353): o 3b executa a tool de leitura mas
        # responde "done/concluído" escondendo o dado, e alucina tools que não
        # chamou. Estas duas linhas atacam a raiz no ponto de reinjeção.
        "- Após ler/listar/buscar: APRESENTE na resposta o conteúdo que a tool "
        "retornou; nunca responda só 'concluído'/'done' sem mostrar o resultado.",
        "- Buscar texto = tool search; lembrar um fato = tool write_memory. NÃO "
        "invente o resultado de uma tool que você não chamou de verdade.",
        # CONV-CONTEXT-LOCATION-HALLUCINATION-01 (#354): o 3b inventa caminhos
        # ao responder "em qual arquivo está X" em conversa longa.
        "- Para dizer ONDE está algo (qual arquivo tem a função/classe/variável X), "
        "use search ou list_files ANTES de responder -- nunca invente um caminho.",
        # EDIT-SEQUENTIAL-OVERWRITE-LOSS-01 (#355): edits sequenciais com write_file
        # sobrescrevem o conteúdo anterior.
        "- Para ADICIONAR ou alterar algo num arquivo que JÁ existe, use edit_file; "
        "se usar write_file, leia o arquivo antes (read_file) e inclua TODO o "
        "conteúdo anterior -- write_file SOBRESCREVE o arquivo inteiro.",
    ]
    if extra:
        lines.append(extra)
    lines.append("</system-reminder>")
    return "\n".join(lines)


# "O prompt é o contrato entre humano e máquina." -- desconhecido
