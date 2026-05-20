"""Classificador rule-based de intent para gating de tools/thinking.

Fonte única importada por proxy.py e loop/_iteration.py.
Sem ML: regex + heurísticas determinísticas.

Categorias:
- 'saudacao': oi/ola/bom dia. Sem tools, sem thinking, num_predict pequeno.
- 'comando':  /help, /clear etc. Tratamento local; não precisa LLM.
- 'tool-needed': verbo imperativo (leia, escreva, liste, grep, etc).
- 'chat': qualquer outra coisa. Sem tools por padrão.
"""

from __future__ import annotations

import re

# Saudacoes curtas. ASCII e acentos; case-insensitive.
# Aceita combinacoes ("ola tudo bem", "oi bom dia") por concatenacao de tokens.
_SAUDACAO_TOKEN = (
    r"(?:oi|ola|olá|hi|hello|hey|salve|"
    r"bom\s+dia|boa\s+tarde|boa\s+noite|"
    r"tudo\s+bem|tudo\s+bom|como\s+vai|"
    r"e\s+ai|eai|opa|alô|alo)"
)
SAUDACOES = re.compile(
    rf"^\s*{_SAUDACAO_TOKEN}(?:[\s\.,!?]+{_SAUDACAO_TOKEN})*[\s\.,!?]*$",
    re.IGNORECASE,
)

# Slash commands locais (sem LLM call).
COMANDOS_CURTOS = re.compile(r"^\s*/[a-z][a-z0-9_\-]*(\s|$)", re.IGNORECASE)

# Verbos imperativos que pedem ferramenta de codigo/IO.
INTENT_TOOL_KEYWORDS = re.compile(
    r"\b("
    r"leia|leu|ler|"
    r"escreva|escrever|edite|editar|"
    r"liste|listar|"
    r"busque|buscar|grep|find|encontre|encontrar|procure|procurar|"
    r"rode|rodar|execute|executar|"
    r"crie|criar|delete|deletar|remova|remover|"
    r"teste|testar|"
    r"mostre|mostrar|abra|abrir|"
    r"baixe|baixar|fetch|download|"
    r"pesquise|pesquisar|"
    r"compile|compilar|build|"
    r"analise|analisar"
    r")\b",
    re.IGNORECASE,
)

# Referências a arquivo/diretório que indicam IO real.
PATH_HINTS = re.compile(
    r"(\.\w{1,6}\b|"  # extensão .py, .md etc
    r"/\w+/|"           # caminho com /
    r"\bREADME\b|"
    r"\barquivo\b|\bdir(?:etorio)?\b|\bpasta\b)",
    re.IGNORECASE,
)


# MEMORY-INTENT-ENFORCE-01: padrões linguísticos PT-BR que sinalizam intent
# de "salvar memória persistente" (deve disparar tool write_memory).
# Cobrem: "lembra que...", "guarda essa info", "anota aí", "memoriza X",
# "registra que eu...", "salva pra depois", "não esquece de X".
# Filosofia "infra > modelo": quando classifier detecta esse intent e o
# modelo não chama write_memory, o proxy faz re-issue com hint forte.
_SAVE_MEMORY_PATTERN = re.compile(
    r"\b("
    r"lembr[ae]\s+(que|de|do|da)|"
    r"lembre[\-\s]*se|"
    r"guarda\s+(essa|isso|esse|esta|este|isto|que)|"
    r"anota\s+(ai|isso|que|aí)|"
    r"memoriz[ae]\s+(que|isso|esse|esta)|"
    r"registr[ae]\s+que|"
    r"salv[ae]\s+(pra|para|essa|isso|isto)|"
    r"n[aã]o\s+esquec[ae]\s+(que|de|do|da|disso)|"
    r"fica\s+(sabendo|de\s+olho)\s+que"
    r")\b",
    re.IGNORECASE,
)


def wants_save_memory(user_input: str) -> bool:
    """Detecta se usuário pediu para salvar memória persistente.

    Usado pelo MEMORY-INTENT-ENFORCE-01 no proxy: quando True E modelo
    não chamou write_memory na resposta, dispara retry 1x com hint forte
    forçando o uso da tool (filosofia "infra > modelo").

    Falso negativo é preferido a falso positivo (não disparar retry sem
    necessidade > forçar retry indevido).
    """
    if not user_input:
        return False
    return bool(_SAVE_MEMORY_PATTERN.search(user_input))


def classify(user_input: str) -> str:
    """Retorna intent: 'saudacao' | 'comando' | 'tool-needed' | 'chat'.

    Ordem de avaliacao:
    1. vazio -> 'chat'
    2. slash command -> 'comando'
    3. saudacao curta (<40 chars, casa regex no inicio) -> 'saudacao'
    4. verbo imperativo OU referencia a arquivo -> 'tool-needed'
    5. default -> 'chat'
    """
    if not user_input:
        return "chat"

    s = user_input.strip()
    if not s:
        return "chat"

    # /help etc tem prioridade sobre saudação (raro, mas seguro).
    if COMANDOS_CURTOS.match(s):
        return "comando"

    # Saudação: precisa ser curta E casar do início até próximo a fim.
    if len(s) < 40 and SAUDACOES.match(s):
        return "saudacao"

    # Verbo imperativo de tool.
    if INTENT_TOOL_KEYWORDS.search(s):
        return "tool-needed"

    # Referência explícita a arquivo/dir -> provavelmente precisa ler.
    if PATH_HINTS.search(s):
        return "tool-needed"

    return "chat"


# "Toda inferência começa por descartar o que não precisa pensar."
