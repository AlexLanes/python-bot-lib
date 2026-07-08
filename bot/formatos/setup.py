# std
from typing import Any, TypeGuard
# interno
from bot.formatos.unmarshaller import Decoders, UnmarshallerError
# externo
import msgspec

def encode_hook (item: object) -> object:
    if (d := getattr(item, "__dict__", None)) is not None:
        return d
    return str(item)

def stringify (item: object, *, indentar: bool = False) -> str:
    """Formatar o `item` para `JSON String`"""
    return msgspec.json.format(
        msgspec.json.encode(item, enc_hook=encode_hook).decode(),
        indent = 4 if indentar else 0
    )

def validar[T] (item: object, formato: type[T]) -> TypeGuard[T]:
    """Validar se o `item` possui o `formato`
    - Retorno `bool`
    #### Exemplo
    ```
    item = [1, 2.0]
    if validar(item, formato=list[int | float]):
        print("lista de int ou float", item)

    assert validar({"a": 1, "b": ""}, formato=dict[str, int]) == False
    assert validar({"a": 1, "b": ""}, formato=dict[str, str | int]) == True
    ```
    """
    try:
        msgspec.convert(item, type=formato, strict=True)
        return True
    except Exception:
        return False

def decode[T] (item: str | bytes, *,
               decoder: Decoders = "json",
               formato: type[T] | Any = Any) -> T:
    """Realizar o decode do `item`, em seu formato `str` `bytes`, usando o `decoder` informado
    - `formato` para validar se o formato do `item` é o esperado"""
    try:
        match decoder:
            case "json": dados = msgspec.json.decode(item)
            case "yaml": dados = msgspec.yaml.decode(item)
            case "toml": dados = msgspec.toml.decode(item)
            case _: raise AssertionError(f"Decoder não esperado em decode({decoder=}, {formato=})")
    except AssertionError: raise
    except Exception as error:
        error = UnmarshallerError(f"Error decode({decoder=}, {formato=}) {error}")
        error.add_note(f"Item: {item}")
        raise error from None

    try: return msgspec.convert(dados, type=formato, strict=False)
    except Exception as error:
        error = UnmarshallerError(f"Error decode({decoder=}, {formato=}) {error}")
        error.add_note(f"Dados: {dados}")
        raise error from None

__all__ = [
    "decode",
    "validar",
    "stringify",
]