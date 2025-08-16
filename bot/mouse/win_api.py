"""Módulo destino as APIs internas do Windows"""

# std
import ctypes
from ctypes import wintypes
# externo
import win32con

send_input = ctypes.windll.user32.SendInput
send_input.argtypes = (wintypes.UINT, ctypes.c_voidp, ctypes.c_int)

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

__all__ = ["send_input_mouse_api"]