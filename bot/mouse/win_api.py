"""Módulo destino as APIs internas do Windows"""

# std
import ctypes
from ctypes import wintypes
from typing import Literal
from time import sleep
# externo
import win32con

send_input = ctypes.windll.user32.SendInput
send_input.argtypes = (wintypes.UINT, ctypes.c_voidp, ctypes.c_int)

type BOTOES_MOUSE = Literal["left", "middle", "right"]
EVENTOS_BOTOES = {
    "left":   (win32con.MOUSEEVENTF_LEFTDOWN,   win32con.MOUSEEVENTF_LEFTUP),
    "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
    "right":  (win32con.MOUSEEVENTF_RIGHTDOWN,  win32con.MOUSEEVENTF_RIGHTUP)
}

class MouseInput (ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class Input (ctypes.Structure):
    class _INPUT (ctypes.Union):
        _fields_ = [("mi", MouseInput)]

    _anonymous_ = ("_input",)
    _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

def send_input_mouse_api (evento: int, dx=0, dy=0, mouse_data=0) -> None:
    input = Input()
    input.type = win32con.INPUT_MOUSE
    input.mi = MouseInput(dx, dy, mouse_data, evento, 0, None)
    send_input(1, ctypes.byref(input), ctypes.sizeof(Input))

def click_mouse_api (delay: float, quantidade: int = 1, botao: BOTOES_MOUSE = "left") -> None:
    """Clicar com o `botão` do mouse `quantidade` vezes na posição atual"""
    assert quantidade >= 1, "Quantidade de clicks deve ser pelo menos 1"

    for _ in range(quantidade):
        for evento in EVENTOS_BOTOES[botao]:
            send_input_mouse_api(evento)
        sleep(delay)

__all__ = [
    "BOTOES_MOUSE",
    "click_mouse_api",
    "send_input_mouse_api",
]