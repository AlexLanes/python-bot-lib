# std
from urllib.parse import urlparse, parse_qs
# interno
from ..estruturas import LowerDict
# externo
from httpx import request, Client, AsyncClient

class Url:
    """Classe para parse de dados de um URL
    - Comparador bool: `bool(url) | if url: ...` True se não for vazio
    - Comparador igualdade: `url1 == url2` True se os urls forem iguais"""

    schema: str
    host: str
    path: str
    query: LowerDict[list[str]]
    url: str

    def __init__ (self, url: str) -> None:
        self.url, parse = url, urlparse(url)
        self.schema, self.host = parse.scheme, parse.hostname
        self.path, self.query = parse.path, LowerDict(parse_qs(parse.query))

    def __repr__ (self) -> str:
        return f"<Url '{self.url}'>"

    def __bool__ (self) -> bool:
        return bool(self.url)

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Url) else self.url == other.url

__all__ = [
    "Url",
    "Client",
    "request",
    "AsyncClient"
]
