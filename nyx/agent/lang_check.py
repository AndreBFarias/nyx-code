"""Detector rule-based pt-BR vs inglês para guardrail de saída (LANG-ENFORCE-01).

Sem ML, sem dependência externa. Regex + listas de marcadores. Falso positivo
preferido a falso negativo: na dúvida, classifica como PT-BR (sem retry).

Casos cobertos:
1. Texto vazio ou < 3 chars -> True (não bloqueia).
2. Tem acento PT-BR (a/e/i/o/u com til/circunflexo/agudo/grave, cedilha) -> True.
3. Senão, conta marcadores PT-BR vs EN; PT-BR vence em empate.

Limitações conhecidas (registradas como não-bugs):
- Código Python/JSON com palavras-chave em inglês ("import", "return") não
  é considerado: este detector roda no content textual da resposta do LLM,
  não em snippets formatados que já foram filtrados de outro modo.
- Nomes próprios em inglês ("GitHub", "Python") não deslocam para EN porque
  não aparecem na lista de marcadores funcionais.

Marcadores PT-BR sem acentuação no regex são intencionais: respostas reais
do qwen3:4b ora vêm acentuadas, ora não; cobrir ambos os formatos aumenta
recall sem perder precisão (acento dispara atalho na função antes do regex).
"""

from __future__ import annotations

import re

# Palavras funcionais frequentes em PT-BR; cobrem saudação, small talk
# e respostas técnicas curtas. Buscar com \b para evitar match dentro de palavras.
# Tokens sem acento são intencionais (cobrem variantes do modelo). noqa-acento
_PT_BR_PATTERN = re.compile(  # noqa-acento
    r"\b("
    r"e|sou|estou|estamos|esta|estao|"
    r"voce|voces|nao|sim|"  # noqa-acento
    r"ola|oi|tudo|bem|bom|boa|dia|tarde|noite|"
    r"obrigad[ao]|por\s+favor|"
    r"aqui|ali|ai|"
    r"posso|podemos|deve|precis[ao]|"
    r"qualquer|tambem|"
    r"para|com|sem|sobre|"
    r"arquivo|diretorio|pasta|projeto|"  # noqa-acento
    r"agente|codigo"
    r")\b",
    re.IGNORECASE,
)

# Marcadores de idiomas não-PT (inglês + italiano + espanhol + francês).
# qwen2.5-coder:3b ocasionalmente responde em italiano para perguntas
# matemáticas ("La somma di 5 + 3 è 8") ou espanhol em frases tecnicas;
# tratar tudo como "não-PT-BR" e disparar retry.
_EN_PATTERN = re.compile(
    r"\b("
    # inglês
    r"the|is|are|am|was|were|be|been|being|"
    r"hello|hi|hey|today|"
    r"help|how|what|when|where|why|which|"
    r"can|could|should|would|will|"
    r"you|your|yours|"
    r"with|without|about|"
    r"please|thank|thanks|"
    r"here|there|"
    r"file|directory|folder|project|"
    # italiano (palavras funcionais distintivas)
    r"sono|della|delle|dello|degli|"
    r"grazie|prego|ciao|"
    r"la\s+somma|che|"
    # espanhol (palavras funcionais distintivas; cuidado para não pegar pt)
    r"hola|estoy|estamos|gracias|"
    r"el|los|las|una|uno|"
    # francês (palavras funcionais distintivas)
    r"bonjour|merci|oui|non|le|les|une|du"
    r")\b",
    re.IGNORECASE,
)

# Acentos EXCLUSIVOS do português (não aparecem em italiano/espanhol/francês).
# 'ã', 'õ' e 'ç' são suficientes para fixar PT-BR sem ambiguidade.
# Acentos compartilhados ('è', 'à', 'é', etc.) NÃO entram aqui — vão pro fallback
# de contagem que distingue por palavras funcionais.
_ACENTO_PT = re.compile(r"[ãõç]", re.IGNORECASE)


def is_pt_br(text: str) -> bool:
    """Retorna True se o texto parece estar em português brasileiro.

    Falso positivo (PT-BR) é preferido a falso negativo (EN) para evitar
    retry desnecessário.
    """
    if not text:
        return True
    stripped = text.strip()
    if len(stripped) < 3:
        return True

    if _ACENTO_PT.search(stripped):
        return True

    pt_hits = len(_PT_BR_PATTERN.findall(stripped))
    en_hits = len(_EN_PATTERN.findall(stripped))

    # Sem marcador algum: não dá pra decidir, assume PT-BR (sem retry).
    if pt_hits == 0 and en_hits == 0:
        return True

    return pt_hits >= en_hits


# IDENTITY-ENFORCE-01: detecção de menção a modelo subjacente.
# ADR-005 (Anonimato) + ADR-027 (Identidade Nyx) são invioláveis.
# Nyx NUNCA pode mencionar nenhum provider proprietário no content de
# resposta — viola identidade. Regex abaixo detecta os principais.  # noqa: ai-mention
_PROVIDER_PATTERN = re.compile(
    r"(?<![a-zA-Z])("
    r"qwen|alibaba|"
    r"gpt|openai|chatgpt|"
    r"claude|anthropic|"  # noqa: ai-mention -- regex de DETECÇÃO, IDENTITY-ENFORCE-01
    r"gemini|bard|"  # noqa: ai-mention -- regex de DETECÇÃO, IDENTITY-ENFORCE-01
    r"copilot|github\s+copilot|"  # noqa: ai-mention -- regex de DETECÇÃO, IDENTITY-ENFORCE-01
    r"llama|meta\s+ai|"
    r"mistral|mixtral|"
    r"deepseek|"
    r"grok|x\s*ai"
    r")(?![a-zA-Z])",
    re.IGNORECASE,
)

# IDENTITY-GUARD-GENERIC-01 (V12): auto-identificação GENÉRICA como IA. A Nyx
# nunca pode se descrever como IA/assistente/modelo (ADR-005/027). _PROVIDER_PATTERN
# pega só NOMES; este pega as frases que vazaram ("como uma inteligência
# artificial", "meus treinamentos", "fui treinado", "modelo de linguagem").
# Ancorado em auto-referência para não disparar em discussão abstrata legítima.  # noqa: ai-mention
_SELF_AI_PATTERN = re.compile(
    r"(intelig[eê]ncia\s+artificial|"
    r"(?<![a-zA-Z])IAs?(?![a-zA-Z])|"
    r"modelo\s+de\s+linguagem|"
    r"(sou|como)\s+(um|uma)\s+(assistente|intelig[eê]ncia|modelo)|"
    r"(meus|nos\s+meus)\s+treinamentos|fui\s+treinad[oa]|"
    r"treinad[oa]\s+(para|por|com|em))",
    re.IGNORECASE,
)


def mentions_provider(text: str) -> str | None:
    """Retorna o primeiro provedor/modelo mencionado, ou None se nenhum.

    Detecta menções a IA proprietária no content da resposta — tanto por
    NOME (_PROVIDER_PATTERN) quanto por auto-identificação GENÉRICA como IA
    (_SELF_AI_PATTERN: "sou uma IA", "meus treinamentos", "modelo de
    linguagem"). ADR-005 e ADR-027 declaram identidade Nyx INVIOLÁVEL —
    qualquer menção quebra contrato. Proxy usa para disparar retry com hint
    anti-vazamento de identidade (espelho de LANG-ENFORCE).

    Returns:
        Trecho casado (lower) se detectado, senão None.
    """
    if not text:
        return None
    m = _PROVIDER_PATTERN.search(text)
    if m:
        return m.group(1).lower()
    m2 = _SELF_AI_PATTERN.search(text)
    return m2.group(0).lower().strip() if m2 else None


# "Idioma é a primeira porta de acolhimento; errar dela quebra confiança."
# "Identidade é a segunda porta; vazar modelo subjacente quebra contrato."
