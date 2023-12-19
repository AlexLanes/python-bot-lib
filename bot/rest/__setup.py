# std
from json import (
    dumps as json_dumps, 
    loads as json_parse
)
# externo
from httpx import request
from jsonschema import validate


def json_stringify (item, indentar=True) -> str:
    """Transforma o `item` em uma string JSON"""
    def tratamentos (obj):
        if isinstance(obj, set): return [x for x in obj]
        if hasattr(obj, "__dict__"): return obj.__dict__
        if hasattr(obj, "__str__"): return obj.__str__()
        raise TypeError(f"Item de tipo inesperado para ser transformado em json: '{ type(item) }'")
    return json_dumps(item, ensure_ascii=False, default=tratamentos, indent=4 if indentar else None)


def validar_schema (item, schema: dict) -> tuple[bool, str | None]:
    """Validar o `item` de acordo com o `schema` informado
    - tuple[0] indicador de sucesso
    - tuple[1] mensagem de erro, caso não resulte em sucesso"""
    try: 
        validate(item, schema)
        return (True, None)
    except Exception as erro:
        return (False, erro.message if hasattr(erro, "message") else "Erro na validação do json_schema")


__all__ = [
    "request",
    "json_parse",
    "json_stringify",
    "validar_schema"
]
