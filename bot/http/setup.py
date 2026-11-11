# std
from email.message import Message
from urllib.parse import urlparse, parse_qs, quote
# interno
from bot.sistema import Caminho
from bot.estruturas import DictNormalizado
from bot.http.cliente import (
    types,
    ClienteHttp,
    ResponseHttp,
    METODOS_HTTP,
)
# externo
import httpx

class Url:
    """Classe para parse de dados de um URL
    - Comparador bool: `bool(url) | if url: ...` True se não for vazio
    - Comparador igualdade: `url1 == url2` True se os urls forem iguais"""

    schema: str
    host: str
    path: str
    query: DictNormalizado[list[str]]
    url: str

    def __init__ (self, url: str) -> None:
        self.url, parse = url, urlparse(url)
        self.schema, self.host = parse.scheme, parse.hostname or ""
        self.path, self.query = parse.path, DictNormalizado(parse_qs(parse.query))

    def __repr__ (self) -> str:
        return f"<Url '{self.url}'>"

    def __bool__ (self) -> bool:
        return bool(self.url)

    def __eq__ (self, other) -> bool:
        return False if not isinstance(other, Url) else self.url == other.url

    @staticmethod
    def encode (path: str) -> str:
        """Codificar o `path` para a versão url encoded"""
        return quote(path)

def request (metodo: METODOS_HTTP,
             url: str,
             query: types.QueryParamTypes | None = None,
             headers: types.HeaderTypes | None = None,
             *,
             json: object | None = None,
             conteudo: types.RequestContent | None = None,
             dados: types.RequestData | None = None,
             arquivos: types.RequestFiles | None = None,
             follow_redirects: bool = False,
             timeout: types.TimeoutTypes = 60,
             verify: str | bool = True) -> ResponseHttp:
    """Realizar um request informando o `método` desejado. Retorna um `ResponseHttp` com métodos adicionais ao `httpx.Response`
    - `metodo` Método HTTP a ser utilizado: `HEAD, OPTIONS, GET, POST, PUT, PATCH, DELETE`
    - `url` URL de destino da requisição: `request("GET", "https://httpbin.org/get")`
    - `query` Parâmetros de query adicionados à URL
        ```
        request("GET", "https://httpbin.org/get", query={ "page": 1, "limit": 10 })
        equivalente à "https://httpbin.org/get?page=1&limit=10"
        ```
    - `headers` Cabeçalhos HTTP enviados na requisição
        ```
        request(
            "GET", "https://httpbin.org/get",
            headers={ "Authorization": "Bearer TOKEN_AQUI", "X-Request-ID": "123" }
        )
        ```
    - `json` Objeto a ser serializado e enviado como JSON no corpo da requisição como `application/json`
    - `dados` Dados enviados como formulário `application/x-www-form-urlencoded`
        ```
        request(
            "POST", "https://api.exemplo.com/login",
            dados={ "username": "xpto", "password": "123" }
        )
        ```
    - `arquivos` Arquivos enviados como `multipart/form-data`
        ```
        request(
            "POST", "https://api.exemplo.com",
            arquivos = {
                "file1": open("arquivo.txt").read(),
                # (Nome arquivo, Bytes ou Stream, MIME Type)
                "file2": ("foto.jpg", open("foto.jpg").read(), "image/jpeg")
            }
        )
        ```
    - `conteudo` Conteúdo bruto (bytes ou string) enviado no corpo da requisição sem o `Header: Content-Type` definido
        ```
        request(
            "POST", "https://api.exemplo.com/xml",
            conteudo = "<user><name>Lucas</name></user>",
            headers = { "Content-Type": "application/xml" }
        )
        ```
    - `follow_redirects` Indica se a requisição deve seguir redirecionamentos automaticamente
    - `timeout` Tempo máximo de espera pela resposta (em segundos).
    - `verify` Define se o certificado SSL deve ser verificado `True/False` ou caminho para o certificado"""
    return (
        ClienteHttp(verify=verify,
                    timeout=timeout,
                    follow_redirects=follow_redirects
        )
        .request(
            metodo=metodo, url=url, query=query, headers=headers,
            json=json, conteudo=conteudo, dados=dados, arquivos=arquivos,
        )
    )

def download (url: str, diretorio: Caminho,
              *,
              chunk_size = 1024 * 1024,
              metodo: METODOS_HTTP = "GET",
              query: types.QueryParamTypes | None = None,
              headers: types.HeaderTypes | None = None,
              follow_redirects: bool = True,
              timeout: types.TimeoutTypes = 60,
              verify: str | bool = True) -> Caminho:
    """Realizar o download de um arquivo para o `diretorio` desejado
    - Feito o stream dos dados para ser mais eficiente
    - Retornado o `Caminho` com o nome do arquivo criado"""
    with httpx.stream(metodo, url, params=query, headers=headers,
                      follow_redirects=follow_redirects, timeout=timeout, verify=verify) as response:
        response.raise_for_status()

        nome_arquivo = ""
        if cd := response.headers.get("Content-Disposition"):
            mensagem = Message()
            mensagem["Content-Disposition"] = cd
            nome_arquivo = mensagem.get_filename()
        nome_arquivo = nome_arquivo or Url(url).path.split("/")[-1]

        destino = diretorio.criar_diretorios() / nome_arquivo
        with open(destino.path, "wb") as writer:
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                writer.write(chunk)

        return destino

__all__ = [
    "Url",
    "request",
    "download",
]