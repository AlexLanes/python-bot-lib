# std
from datetime import datetime, date, time
from typing import Literal, Iterable, Protocol, Sized

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

type tipoSQL = primitivo | bytes | date | time | datetime 
"""Tipos possível de retorno do ResultadoSQL"""
type nomeado = dict[str, tipoSQL]
"""Parâmetros necessários quando o SQL é nomeado ':nome'"""
type posicional = Iterable[tipoSQL]
"""Parâmetros necessários quando o SQL é posicionail '?'"""

DIRECOES_SCROLL = Literal["cima", "baixo"]
"""Direções de scroll do mouse"""
BOTOES_MOUSE = Literal["left", "middle", "right"]
"""Botões aceitos pelo `pynput`"""
PORCENTAGENS = Literal["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1"] | float
"""Porcentagens (float) entre 0.0 e 1.0"""
BOTOES_TECLADO = Literal["alt", "alt_l", "alt_r", "alt_gr", "backspace", "caps_lock", "cmd", "cmd_r", "ctrl", "ctrl_l", "ctrl_r", "delete", "down", "end", "enter", "esc", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19", "f20", "f21", "f22", "f23", "f24", "home", "left", "page_down", "page_up", "right", "shift", "shift_r", "space", "tab", "up", "media_play_pause", "media_volume_mute", "media_volume_down", "media_volume_up", "media_previous", "media_next", "insert", "menu", "num_lock", "pause", "print_screen", "scroll_lock"]
"""Botões especiais aceitos pelo `pynput`"""

class _SupportsBool (Protocol):
    def __bool__ (self) -> bool: ...
type SupportsBool = _SupportsBool | Sized
"""Tipo indicador de qualquer objeto que suporte `bool(objeto)`"""

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