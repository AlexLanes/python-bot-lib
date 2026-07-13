# std
import typing
# interno
from bot.estruturas import DictNormalizado
from bot.formatos import ElementoXML, validar, Unmarshaller
# externo
import httpx

class ResponseHttp (httpx.Response):
    """Response extensão do `httpx.Response` com métodos para facilitar validação de uma resposta http"""

    @classmethod
    def New (cls, response: httpx.Response) -> typing.Self:
        obj = super().__new__(cls)
        obj.__dict__ = response.__dict__

        try: setattr(obj, "_headers", response.headers)
        except Exception: pass

        return obj

    @property
    def headers_dict (self) -> dict[str, str]:
        """Headers com chaves normalizadas
        - `Chaves` dos headers em `lower` e feito `strip()`
        - `Valores` dos headers transformados em `str`
        - Caso existam múltiplos headers de mesmo nome, os valores serão concatenados por `,`"""
        return {
            str(key).lower().strip(): str(value)
            for key, value in dict(getattr(self, "_headers", {})).items()
        }

    @property
    def headers (self) -> DictNormalizado[str]:
        """Headers com chaves normalizadas
        - Caso existam múltiplos headers de mesmo nome, os valores serão concatenados por `,`"""
        return DictNormalizado(self.headers_dict)

    def esperar_sucesso (self, mensagem: str | None = None) -> typing.Self:
        """Fazer o `assert` se o `response.status_code` de retorno é `2xx`
        - `mensagem` sobrescreve a mensagem utilizada como erro"""
        if self.is_success:
            return self

        msg_status = f"Status code de Resposta HTTP '{self.status_code}' não é de sucesso"
        if mensagem:
            erro = AssertionError(mensagem)
            erro.add_note(msg_status)
        else: erro = AssertionError(msg_status)

        raise erro

    def esperar_status_code (self, status: int, mensagem: str | None = None) -> typing.Self:
        """Fazer o `assert` se `response.status_code == status`
        - `mensagem` sobrescreve a mensagem utilizada como erro"""
        if self.status_code == status:
            return self

        msg_status = f"Status code de Resposta HTTP '{self.status_code}' diferente do esperado '{status}'"
        if mensagem:
            erro = AssertionError(mensagem)
            erro.add_note(msg_status)
        else: erro = AssertionError(msg_status)

        raise erro

    def esperar_tipo_conteudo (self, tipo: str, mensagem: str | None = None) -> typing.Self:
        """Fazer o `assert` se `tipo` está no `Header: Content-Type`
        - `mensagem` sobrescreve a mensagem utilizada como erro"""
        content_type = self.headers.get("Content-Type", "").lower()
        if tipo.lower() in content_type:
            return self

        msg_conteudo = f"Content-Type de Resposta HTTP '{content_type}' diferente do esperado '{tipo}'"
        if mensagem:
            erro = AssertionError(mensagem)
            erro.add_note(msg_conteudo)
        else: erro = AssertionError(msg_conteudo)

        raise erro

    @property
    def conteudo (self) -> bytes:
        """Ler todo o conteúdo do corpo como `bytes`"""
        return self.content

    @property
    def texto (self) -> str:
        """Ler todo o conteúdo do corpo e decodificar para `str`"""
        return self.text

    def xml (self) -> ElementoXML:
        """Realizar o parse do conteúdo de resposta como um `ElementoXML`
        - `ValueError` caso ocorra erro de parse"""
        try: return ElementoXML.Parse(self.texto)
        except Exception as erro:
            raise ValueError("Erro ao realizar o parse para XML da Resposta HTTP") from erro

    @typing.overload
    def json (self) -> typing.Any: ... # type: ignore
    @typing.overload
    def json[T] (self, esperar: type[T]) -> T: ... # type: ignore
    @typing.override
    def json[T] (self, esperar: type[T] = typing.Any) -> T | typing.Any: # type: ignore
        """Realizar o parse do conteúdo de resposta como o tipo `esperar`
        - `esperar`: `dict[str, str | int]`, `list[dict[str, str]]`
        - `ValueError` caso ocorra erro de parse"""
        try: json = super().json()
        except Exception as erro:
            raise ValueError("Erro ao realizar o parse para JSON da Resposta HTTP") from erro

        if validar(json, esperar):
            return json
        raise ValueError(f"Erro ao realizar a validação do JSON da Resposta HTTP para o tipo esperado '{esperar}'")

    def unmarshal[T: Unmarshaller] (self, cls: type[T]) -> T:
        """Realizar o Unmarshal do conteúdo `json` conforme a classe anotada `cls`
        - Resposta deve ser um json `dict`
        - `ValueError`

        ### Exemplo
        ```
        from bot.http import request
        from bot.formatos import Unmarshaller

        class Dimensions (Unmarshaller):
            width: float
            height: float
            depth: float
        class Product (Unmarshaller):
            id: int
            title: str
            category: str
            price: float
            tags: list[str]
            dimensions: Dimensions

        produto = request("GET", "https://dummyjson.com/products/1").unmarshal(Product)
        print(produto.id)
        print(produto.stringify(indent=True))
        ```
        """
        json = self.json()
        try: return cls.Unmarshal(json)
        except Exception as erro:
            raise ValueError(f"Erro ao realizar o Unmarshal da Resposta HTTP para '{cls}'") from erro

    def unmarshal_many[T: Unmarshaller] (self, cls: type[T]) -> list[T]:
        """Realizar o Unmarshal do conteúdo `json` conforme a classe anotada `cls`
        - Resposta deve ser um json `list[dict]`
        - `ValueError`"""
        json = self.json()
        try: return cls.UnmarshalMany(json)
        except Exception as erro:
            raise ValueError(f"Erro ao realizar o Unmarshal da Resposta HTTP para '{cls}'") from erro

__all__ = ["ResponseHttp"]