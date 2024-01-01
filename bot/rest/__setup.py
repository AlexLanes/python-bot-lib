# externo
from httpx import request
from jsonschema import validate


def validar_schema (item, schema: dict) -> tuple[bool, str | None]:
    """Validar o `item` de acordo com o `schema` informado
    - tuple[0] indicador de sucesso
    - tuple[1] mensagem de erro, caso não resulte em sucesso"""
    try: 
        validate(item, schema)
        return (True, None)
    except Exception as erro:
        return (False, erro.message if hasattr(erro, "message") else "Erro na validação do jsonschema")


__all__ = [
    "request",
    "validar_schema",
]
