"""Superclasse e exceções comuns para providers de inferência.

Define ``ProviderError`` -- wrapper canônico de qualquer falha de rede,
timeout ou protocolo vinda de provider externo (httpx, urllib3 etc).
O handler do REPL (cli.py / loop) sempre recebe ``ProviderError`` com
``user_message`` em PT-BR e ``hint`` acionável, evitando vazar strings
em inglês para o usuário (ERROR-MSG-01).
"""

from __future__ import annotations


class ProviderError(Exception):
    """Erro canônico de provider de inferência.

    Atributos:
      user_message -- mensagem em PT-BR pronta para exibição via print_error.
      hint -- verbo imperativo acionável (ex: 'Verifique systemctl status ollama').
      cause -- exceção original (httpx.ReadTimeout, httpx.ConnectError etc).

    Uso canônico::

        try:
            ...
        except httpx.ReadTimeout as e:
            raise ProviderError(
                user_message="Ollama não respondeu em 30s.",
                hint="Verifique se está rodando: systemctl status ollama",
                cause=e,
            )
    """

    def __init__(
        self,
        user_message: str,
        hint: str | None = None,
        cause: BaseException | None = None,
    ) -> None:
        self.user_message = user_message
        self.hint = hint
        self.cause = cause
        detail = user_message
        if hint:
            detail += f" ({hint})"
        super().__init__(detail)


# "A clareza no aviso é o primeiro ato de respeito ao outro." -- Epicteto (adaptado)
