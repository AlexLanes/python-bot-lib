type url = str
"""String formato url"""
type char = str
"""String com 1 caractere"""
type email = str
"""String formato E-mail"""
type rgb = tuple[int, int, int]
"""Tipo da cor RGB"""
type primitivo = str | int | float | bool | None
"""Tipos primitivos do Python"""

type TJson = primitivo | dict[str, TJson] | list[TJson]
"""Tipos do Python que pertencem ao mesmo formato do `Json`"""
type Numerico = int | float
"""Tipos númericos primitivos do Python
- `bool` é uma implementação do `int`"""
type SupportsStr = str | object
"""Tipo indicador de qualquer objeto que suporte `str(objeto)`"""
type SupportsBool = bool | object
"""Tipo indicador de qualquer objeto que suporte `bool(objeto)`"""

__all__ = [
    "url",
    "rgb",
    "char",
    "email",
    "TJson",
    "Numerico",
    "primitivo",
    "SupportsStr",
    "SupportsBool",
]