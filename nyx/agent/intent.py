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

# PROXY-INTENT-CODE-BUDGET-01 (#352a): verbos que PRODUZEM/ALTERAM código ou
# arquivo. A saída é longa (um write_file/edit_file com o conteúdo inteiro), logo
# precisa do budget 'code' (4096), não 'tool' (2048) que trunca o JSON do tool_call.
INTENT_CODE_KEYWORDS = re.compile(
    r"\b("
    r"escreva|escrever|escreve|"
    r"edite|editar|edita|"
    r"crie|criar|cria|"
    r"reescreva|reescrever|reescreve|"
    r"gere|gerar|gera|"
    r"implemente|implementar|implementa|"
    r"adicione|adicionar|adiciona|"
    r"refatore|refatorar|refatora|"
    r"corrija|corrigir|corrige|"
    r"modifique|modificar|modifica"
    r")\b",
    re.IGNORECASE,
)

# Contexto que confirma alvo de código/arquivo (evita classificar "crie uma
# lista" como code). Complementa PATH_HINTS com termos de programação.
_CODE_CONTEXT = re.compile(
    r"\b(c[oó]digo|fun[cç][aã]o|m[eé]todo|classe|script|"
    r"def|class|import|argparse|README|"
    r"arquivo|m[oó]dulo)\b|\.\w{1,6}\b",
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
    4. escrita/geracao de codigo (verbo de escrita + alvo de arquivo/codigo) -> 'code'
    5. verbo imperativo OU referencia a arquivo -> 'tool-needed'
    6. default -> 'chat'
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

    # PROXY-INTENT-CODE-BUDGET-01 (#352a): escrita/geração de código ou arquivo
    # -> 'code' (budget 4096). Exige verbo de escrita E alvo de arquivo/código
    # (PATH_HINTS ou _CODE_CONTEXT), para não inflar o budget de pedidos genéricos.
    if INTENT_CODE_KEYWORDS.search(s) and (PATH_HINTS.search(s) or _CODE_CONTEXT.search(s)):
        return "code"

    # Verbo imperativo de tool.
    if INTENT_TOOL_KEYWORDS.search(s):
        return "tool-needed"

    # Referência explícita a arquivo/dir -> provavelmente precisa ler.
    if PATH_HINTS.search(s):
        return "tool-needed"

    # MEMORY-INTENT-CLASSIFY-01: pedido de salvar memória ("lembra que X",
    # "guarda essa info") precisa da tool write_memory. Sem isto, cai em 'chat'
    # (tools=[]) e o modelo alucina "lembrado" sem gravar -- achado do estresse
    # da ONDA-44. wants_save_memory já existe e é a fonte única do padrão.
    if wants_save_memory(s):
        return "tool-needed"

    return "chat"


# "Toda inferência começa por descartar o que não precisa pensar."
