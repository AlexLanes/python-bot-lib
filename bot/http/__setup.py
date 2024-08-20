# std
from urllib.parse import urlparse, parse_qs
# externo
from httpx import request, Client, AsyncClient

class Headers:
    """Classe usada para obter/criar headers como lower-case
    - Obter: `headers["nome"]` KeyError caso não exista
    - Checar existência: `"nome" in headers`
    - Adicionar/Atualizar: `headers["nome"] = "valor"`
    - Tamanho: `len(headers)` quantidade de headers
    - Comparador bool: `bool(headers) | if headers: ...` True se não for vazio
    - Comparador igualdade: `headers1 == headers2` True se os headers e valores forem iguais"""

    headers: dict[str, str]

    def __init__ (self, headers: dict[str, str] | None = None) -> None:
        self.headers = {
            chave.lower().strip(): valor
            for chave, valor in (headers or {}).items()
        }

    def __repr__ (self) -> str:
        return f"<Headers com '{len(self)}' chaves>"

    def __getitem__ (self, nome: str) -> str:
        return self.headers[nome.strip().lower()]

    def __setitem__ (self, nome: str, valor: str) -> None:
        self.headers[nome.lower().strip()] = valor

    def __contains__ (self, chave: str) -> bool:
        return chave.lower().strip() in self.headers

    def __len__ (self) -> int:
        return len(self.headers)

    def __bool__ (self) -> bool:
        return bool(self.headers)

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Headers) else all(
            header in other and header == other.headers[header]
            for header in self.headers
        ) and len(self) == len(other)

    @property
    def __dict__ (self) -> dict[str, str]:
        return self.headers

class Url:
    """Classe para parse de dados de um URL
    - Comparador bool: `bool(url) | if url: ...` True se não for vazio
    - Comparador igualdade: `url1 == url2` True se os urls forem iguais"""

    schema: str
    host: str
    path: str
    query: dict[str, list[str]]
    url: str

    def __init__ (self, url: str) -> None:
        self.url, parse = url, urlparse(url)
        self.schema, self.host = parse.scheme, parse.hostname
        self.path, self.query = parse.path, parse_qs(parse.query)

    def __repr__ (self) -> str:
        return f"<Url '{self.url}'>"

    def __bool__ (self) -> bool:
        return bool(self.url)

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Url) else self.url == other.url

__all__ = [
    "Url",
    "Client",
    "Headers",
    "request",
    "AsyncClient"
]
