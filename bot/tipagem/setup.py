# std
from typing import Literal, Iterable
from datetime import datetime, date, time

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
type SupportsBool = object
"""Tipo indicador de qualquer objeto que suporte `bool(objeto)`"""

type tipoSQL = primitivo | bytes | date | time | datetime 
"""Tipos possível de retorno do ResultadoSQL"""
type nomeado = dict[str, tipoSQL]
"""Parâmetros necessários quando o SQL é nomeado ':nome'"""
type posicional = Iterable[tipoSQL]
"""Parâmetros necessários quando o SQL é posicional '?'"""

DIRECOES_SCROLL = Literal["cima", "baixo"]
"""Direções de scroll aceitos pelo `bot.mouse`"""
BOTOES_MOUSE = Literal["left", "middle", "right"]
"""Nome dos botões aceitos pelo `bot.mouse`"""
PORCENTAGENS = float | Literal["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1"]
"""Porcentagens (float) entre 0.0 e 1.0"""
BOTOES_TECLADO = Literal["alt", "ctrl", "shift", "alt_gr", "backspace", "win", "enter", "esc", "space", "tab", "up", "down", "left", "right", "insert", "delete", "home", "end", "page_down", "page_up", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19", "f20", "f21", "f22", "f23", "f24"]
"""Nome dos botões virtuais aceitos pelo `bot.teclado`"""

__all__ = [
    "url",
    "rgb",
    "char",
    "email",
    "tipoSQL",
    "nomeado",
    "primitivo",
    "posicional",
    "BOTOES_MOUSE",
    "PORCENTAGENS",
    "SupportsBool",
    "BOTOES_TECLADO",
    "DIRECOES_SCROLL",
]