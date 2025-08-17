"""Módulo para tratar mensagem de rede de perfomance do Chrome"""

# std
from typing import Any
# interno
import bot

class Response:

    status: int
    headers: bot.estruturas.LowerDict
    body: Any

    def __init__ (self) -> None:
        self.headers = bot.estruturas.LowerDict()

    def __getattr__ (self, nome: str) -> None:
        return None

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Response) else all(
            getattr(self, atributo, None) == getattr(other, atributo, None)
            for atributo in ("status", "headers", "body")
        )

class Request:

    url: bot.http.Url
    metodo: str
    headers: bot.estruturas.LowerDict
    body: Any

    def __init__ (self) -> None:
        self.url, self.headers = bot.http.Url(""), bot.estruturas.LowerDict()

    def __getattr__ (self, nome: str) -> None:
        return None

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Request) else all(
            getattr(self, atributo, None) == getattr(other, atributo, None)
            for atributo in ("url", "metodo", "headers", "body")
        )

class Mensagem:

    request: Request
    response: Response

    def __init__ (self) -> None:
        self.request, self.response = Request(), Response()

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Mensagem) else all(
            getattr(self, atributo) == getattr(other, atributo)
            for atributo in ("request", "response")
        )

    def parse_request (self, params: bot.formatos.Json) -> None:
        self.request = self.request or Request()
        if not self.request.url and params.request.url:
            self.request.url = bot.http.Url(params.request.url.obter(Any) or "")
        if not self.request.metodo and params.request.method:
            self.request.metodo = params.request.method.obter(Any)
        if not self.request.body and params.request.postData:
            self.request.body = params.request.postData.obter(Any)
        if headers := (params.headers or params.request.headers).obter(Any):
            self.request.headers = self.request.headers or bot.estruturas.LowerDict()
            for header in headers:
                self.request.headers[header] = headers[header]

    def parse_response (self, params: bot.formatos.Json) -> None:
        self.response = self.response or Response()
        if not self.response.status and params.response.status:
            self.response.status = params.response.status.obter(Any)
        if headers := (params.headers or params.response.headers).obter(Any):
            self.response.headers = self.response.headers or bot.estruturas.LowerDict()
            for header in headers:
                self.response.headers[header] = headers[header]

__all__ = ["Mensagem"]