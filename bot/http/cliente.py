# std
import typing
# interno
from bot.http.response import ResponseHttp
# externo
import httpx
import httpx._types as types
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault

type METODOS_HTTP = typing.Literal["HEAD", "OPTIONS", "GET", "POST", "PUT", "PATCH", "DELETE"]

class ClienteHttp (httpx.Client):
    """Criar um cliente `HTTP` para realizar requests. Extensão do `httpx.Client`
    - Veja a documentação do `request()` para informação sobre todos os parâmetros aceitos
    - Retorno dos métodos `request, get, post, put, ...` é um `ResponseHttp` com métodos adicionais ao `httpx.Response`"""

    @typing.override
    def request (self, metodo: METODOS_HTTP, # type: ignore
                       url: str,
                       query: types.QueryParamTypes | None = None,
                       headers: types.HeaderTypes | None = None,
                       *,
                       json: object | None = None,
                       conteudo: types.RequestContent | None = None,
                       dados: types.RequestData | None = None,
                       arquivos: types.RequestFiles | None = None,
                       follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                       timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request informando o `método` desejado
        - `metodo` Método HTTP a ser utilizado: `HEAD, OPTIONS, GET, POST, PUT, PATCH, DELETE`
        - `url` URL de destino da requisição
            ```
            ClienteHttp().request("GET", "https://httpbin.org/get")
            ClienteHttp(base_url="https://httpbin.org").request("GET", "/get")
            ```
        - `query` Parâmetros de query adicionados à URL
            ```
            client.request("GET", "https://httpbin.org/get", query={ "page": 1, "limit": 10 })
            equivalente à "https://httpbin.org/get?page=1&limit=10"
            ```
        - `headers` Cabeçalhos HTTP enviados na requisição
            ```
            client.request(
                "GET", "https://httpbin.org/get",
                headers={ "Authorization": "Bearer TOKEN_AQUI", "X-Request-ID": "123" }
            )
            ```
        - `json` Objeto a ser serializado e enviado como JSON no corpo da requisição como `application/json`
        - `dados` Dados enviados como formulário `application/x-www-form-urlencoded`
            ```
            client.request(
                "POST", "https://api.exemplo.com/login",
                dados={ "username": "xpto", "password": "123" }
            )
            ```
        - `arquivos` Arquivos enviados como `multipart/form-data`
            ```
            client.request(
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
            client.request(
                "POST", "https://api.exemplo.com/xml",
                conteudo = "<user><name>Lucas</name></user>",
                headers = { "Content-Type": "application/xml" }
            )
            ```
        - `follow_redirects` Indica se a requisição deve seguir redirecionamentos automaticamente
        - `timeout` Tempo máximo de espera pela resposta (em segundos).
        - `verify` Define se o certificado SSL deve ser verificado `True/False` ou caminho para o certificado"""
        response = super().request(
            metodo, url, params=query, headers=headers,
            json=json, content=conteudo, data=dados, files=arquivos,
            follow_redirects=follow_redirects, timeout=timeout
        )
        return ResponseHttp.new(response)

    @typing.override
    def get (self, url: str, # type: ignore
                   query: types.QueryParamTypes | None = None,
                   headers: types.HeaderTypes | None = None,
                   *,
                   follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                   timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `GET`"""
        return self.request("GET", url, query, headers, follow_redirects=follow_redirects, timeout=timeout)

    @typing.override
    def head (self, url: str, # type: ignore
                    query: types.QueryParamTypes | None = None,
                    headers: types.HeaderTypes | None = None,
                    *,
                    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                    timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `HEAD`"""
        return self.request("HEAD", url, query, headers, follow_redirects=follow_redirects, timeout=timeout)

    @typing.override
    def options (self, url: str, # type: ignore
                       query: types.QueryParamTypes | None = None,
                       headers: types.HeaderTypes | None = None,
                       *,
                       follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                       timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `OPTIONS`"""
        return self.request("OPTIONS", url, query, headers, follow_redirects=follow_redirects, timeout=timeout)

    @typing.override
    def delete (self, url: str, # type: ignore
                      query: types.QueryParamTypes | None = None,
                      headers: types.HeaderTypes | None = None,
                      *,
                      follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                      timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `DELETE`"""
        return self.request(
            "DELETE", url, query, headers, 
            follow_redirects=follow_redirects, timeout=timeout
        )

    @typing.override
    def post (self, url: str, # type: ignore
                    query: types.QueryParamTypes | None = None,
                    headers: types.HeaderTypes | None = None,
                    *,
                    json: object | None = None,
                    conteudo: types.RequestContent | None = None,
                    dados: types.RequestData | None = None,
                    arquivos: types.RequestFiles | None = None,
                    follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                    timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `POST`"""
        return self.request(
            "POST", url, query, headers, 
            json=json, conteudo=conteudo, dados=dados, arquivos=arquivos,
            follow_redirects=follow_redirects, timeout=timeout
        )

    @typing.override
    def put (self, url: str, # type: ignore
                   query: types.QueryParamTypes | None = None,
                   headers: types.HeaderTypes | None = None,
                   *,
                   json: object | None = None,
                   conteudo: types.RequestContent | None = None,
                   dados: types.RequestData | None = None,
                   arquivos: types.RequestFiles | None = None,
                   follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                   timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `PUT`"""
        return self.request(
            "PUT", url, query, headers, 
            json=json, conteudo=conteudo, dados=dados, arquivos=arquivos,
            follow_redirects=follow_redirects, timeout=timeout
        )

    @typing.override
    def patch (self, url: str, # type: ignore
                     query: types.QueryParamTypes | None = None,
                     headers: types.HeaderTypes | None = None,
                     *,
                     json: object | None = None,
                     conteudo: types.RequestContent | None = None,
                     dados: types.RequestData | None = None,
                     arquivos: types.RequestFiles | None = None,
                     follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                     timeout: types.TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT) -> ResponseHttp:
        """Realizar um request `PATCH`"""
        return self.request(
            "PATCH", url, query, headers, 
            json=json, conteudo=conteudo, dados=dados, arquivos=arquivos,
            follow_redirects=follow_redirects, timeout=timeout
        )

__all__ = ["ClienteHttp"]