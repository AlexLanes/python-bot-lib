# std
from typing import Literal, Iterable
from datetime import datetime, date, time


type url = str
"""String formato url"""
type char = str
"""String com 1 caractere"""
type email = str
"""String formato E-mail"""
type caminho = str
"""Caminho relativo ou absoluto"""
type primitivo = str | int | float | bool | None
"""Tipos primitivos do Python"""

type tipoSQL = primitivo | date | time | datetime 
"""Tipos possível de retorno do ResultadoSQL"""
type nomeado = dict[str, tipoSQL]
"""Parâmetros necessários quando o SQL é nomeado ':nome'"""
type posicional = Iterable[tipoSQL]
"""Parâmetros necessários quando o SQL é posicionail '?'"""


DIRECOES_SCROLL = Literal["cima", "baixo"]
"""Direções de scroll do mouse"""
BOTOES_MOUSE = Literal["left", "middle", "right"]
"""Botões aceitos pelo `pynput`"""
PORCENTAGENS = Literal["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1"]
"""Porcentagens de confiança aceitos pelo `PyScreeze` e `EasyOCR`, entre 1.0 e 0.0"""
ESTRATEGIAS_WEBELEMENT = Literal["id", "xpath", "link text", "name", "tag name", "class name", "css selector", "partial link text"]
"""Estratégias para a localização de WebElements no `Selenium`"""
BOTOES_TECLADO = Literal["alt", "alt_l", "alt_r", "alt_gr", "backspace", "caps_lock", "cmd", "cmd_r", "ctrl", "ctrl_l", "ctrl_r", "delete", "down", "end", "enter", "esc", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19", "f20", "f21", "f22", "f23", "f24", "home", "left", "page_down", "page_up", "right", "shift", "shift_r", "space", "tab", "up", "media_play_pause", "media_volume_mute", "media_volume_down", "media_volume_up", "media_previous", "media_next", "insert", "menu", "num_lock", "pause", "print_screen", "scroll_lock"]
"""Botões especiais aceitos pelo `pynput`"""
BACKENDS_JANELA = Literal["win32", "uia"]
"""Backends aceitos pelo `pywinauto`"""


__all__ = [
    "url",
    "char",
    "email",
    "tipoSQL",
    "nomeado",
    "caminho",
    "primitivo",
    "posicional",
    "BOTOES_MOUSE",
    "PORCENTAGENS",
    "BOTOES_TECLADO",
    "DIRECOES_SCROLL",
    "BACKENDS_JANELA",
    "ESTRATEGIAS_WEBELEMENT"
]
