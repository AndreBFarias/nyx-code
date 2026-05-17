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

_EN_PATTERN = re.compile(
    r"\b("
    r"the|is|are|am|was|were|be|been|being|"
    r"hello|hi|hey|today|"
    r"help|how|what|when|where|why|which|"
    r"can|could|should|would|will|"
    r"you|your|yours|"
    r"with|without|about|"
    r"please|thank|thanks|"
    r"here|there|"
    r"file|directory|folder|project"
    r")\b",
    re.IGNORECASE,
)

# Acentos específicos do português. Suficiente para fixar PT-BR sem ambiguidade.
_ACENTO_PT = re.compile(r"[áéíóúâêîôûãõàèç]", re.IGNORECASE)


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


# "Idioma é a primeira porta de acolhimento; errar dela quebra confiança."
