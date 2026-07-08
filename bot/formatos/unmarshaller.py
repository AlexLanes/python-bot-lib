# std
from base64 import b64decode
from typing import (
    Any, Self, Literal,
    Mapping, Iterable,
    overload,
)
# interno
from bot.sistema import Caminho
# externo
import msgspec

type Encoders = Literal["json", "yaml", "toml"]
type Decoders = Encoders

class UnmarshallerError (Exception):
    """Erros do `Unmarshaller` ao realizar a transformação para um Modelo"""

class Unmarshaller (msgspec.Struct):
    """Classe Base usada para transformação de um `dict` para uma Classe Modelo
    - Parâmetro `strict=False` faz conversões de dados para o Python quando possível
    - Exception utilizada `from bot.formatos.unmarshaller import UnmarshallerError`

    ### Parâmetros aceitos pela `MetaClass`
    ```
    class Dados (
        Unmarshaller,
        eq: bool = True, # Adicionar o comparador ==
        order: bool = False, # Adicionar os comparadores < >= < <=
        kw_only: bool = False, # Restringir o __init__ com argumentos nomeados
        rename: dict[str, str] = None, # Nomes alternativos das propriedades
        forbid_unknown_fields: bool = False, # Restringir propriedades não especificadas
    )    
    ```

    ### Exemplo
    ```
    from enum import Enum
    from decimal import Decimal
    from datetime import date, datetime

    from bot.formatos.unmarshaller import Unmarshaller, UnmarshallerError

    class Tag (Enum):
        ADMIN = "admin"
        PREMIUM = "premium"
        BETA = "beta"
    class Endereco(Unmarshaller):
        rua: str
        numero: int
        cidade: str
        uf: str
        cep: str
    class Pessoa (Unmarshaller, rename={"id": "id pessoa"}):
        id: int
        nome: str
        ativo: bool
        idade: int | None
        salario: float
        credito: Decimal
        nascimento: date
        ultimo_acesso: datetime
        tags: list[Tag]
        endereco: Endereco
        configuracoes: dict[str, str]
        opcional: str | None = None

    pessoa = Pessoa.Unmarshal({
        "id pessoa": 1,
        "nome": "Alex Lanes",
        "ativo": True,
        "idade": 29,
        "salario": 3500.75,
        "credito": "1250.50",
        "nascimento": "1998-04-15",
        "tags": ["admin", "premium"],
        "ultimo_acesso": "2026-07-08T14:30:15",
        "endereco": {
            "rua": "Rua das Flores",
            "numero": 123,
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01000-000"
        },
        "configuracoes": {
            "tema": "escuro",
            "idioma": "pt-BR"
        }
    })
    print(pessoa.id, pessoa.nome)
    print(pessoa.as_dict())
    print(pessoa.encode(encoder="json"))
    ```
    """

    @classmethod
    def Unmarshal (cls, data: Mapping[str, Any], *, strict=False) -> Self:
        try: return msgspec.convert(data, cls, strict=strict)
        except Exception as error:
            error = UnmarshallerError(f"Error {cls.__name__}.Unmarshal({strict=}) {error}")
            error.add_note(f"Data: {data}")
            raise error from None

    @classmethod
    def UnmarshalMany (cls, data: Iterable[Mapping[str, Any]], *, strict=False) -> list[Self]:
        try: return msgspec.convert(data, list[cls], strict=strict)
        except Exception as error:
            error = UnmarshallerError(f"Error {cls.__name__}.UnmarshalMany({strict=}) {error}")
            error.add_note(f"Data: {data}")
            raise error from None

    @overload
    @classmethod
    def Decode (cls, data: bytes | str, *, decoder: Decoders = "json", strict=False) -> Self: ...
    @overload
    @classmethod
    def Decode (cls, data: Caminho, *, decoder: Decoders = "json", strict=False) -> Self: ...
    @classmethod
    def Decode (cls, data: bytes | str | Caminho, *, decoder: Decoders = "json", strict=False) -> Self:
        if isinstance(data, Caminho):
            try: data = data.ler_bytes()
            except Exception as error:
                error = UnmarshallerError(f"Error {cls.__name__}.Decode({decoder=}, {strict=}) {error}")
                error.add_note(f"Caminho: {data}")
                raise error from None

        try:
            match decoder:
                case "json": return msgspec.json.decode(data, type=cls, strict=strict)
                case "yaml": return msgspec.yaml.decode(data, type=cls, strict=strict)
                case "toml": return msgspec.toml.decode(data, type=cls, strict=strict)
        except Exception as error:
            error = UnmarshallerError(f"Error {cls.__name__}.Decode({decoder=}, {strict=}) {error}")
            error.add_note(f"Data: {data}")
            raise error from None

        raise ValueError(f"Decoder não esperado em {self.__class__.__name__}.Decode({decoder=}, {strict=})")

    @classmethod
    def DecodeB64 (cls, data: str, *, decoder: Decoders = "json", strict=False) -> Self:
        decoded = b64decode(data)
        return cls.Decode(decoded, decoder=decoder, strict=strict)

    def as_dict (self) -> dict[str, Any]:
        return {
            nome: (
                v.as_dict()
                if isinstance(v := getattr(self, nome), Unmarshaller)
                else v
            )
            for nome in self.__struct_fields__
        }

    def encode (self, *, encoder: Encoders = "json") -> bytes:
        data = self.as_dict()
        match encoder:
            case "json": return msgspec.json.encode(data)
            case "yaml": return msgspec.yaml.encode(data)
            case "toml": return msgspec.toml.encode(data)
            case _: raise ValueError(f"Encoder não esperado em {self.__class__.__name__}().encode({encoder=})")

    def stringify (self, *, indent: bool = False) -> str:
        """Formatar o `Modelo` para `JSON String`"""
        data = self.as_dict()
        return msgspec.json.format(
            msgspec.json.encode(data).decode(),
            indent = 4 if indent else 0
        )

__all__ = [
    "Unmarshaller",
    "UnmarshallerError",
]