"""Módulo destino as APIs internas do Windows"""

# std
import ctypes
from ctypes import wintypes
# interno
from bot.estruturas import LowerDict
# externo
import win32con

send_input = ctypes.windll.user32.SendInput
send_input.argtypes = (wintypes.UINT, ctypes.c_voidp, ctypes.c_int)

virtual_key_scan_w = ctypes.windll.user32.VkKeyScanW
virtual_key_scan_w.restype = wintypes.SHORT
virtual_key_scan_w.argtypes = (wintypes.WCHAR,)

CODIGOS_VK_TECLAS_EXTENDIDAS = (win32con.VK_HOME, win32con.VK_END, win32con.VK_INSERT, win32con.VK_DELETE,
                                win32con.VK_UP, win32con.VK_DOWN, win32con.VK_LEFT, win32con.VK_RIGHT,
                                win32con.VK_PRIOR, win32con.VK_NEXT)
CODIGOS_VK_TECLAS = LowerDict({
    "alt": win32con.VK_MENU,
    "ctrl": win32con.VK_CONTROL,
    "shift": win32con.VK_SHIFT,
    "alt_gr": win32con.VK_RMENU,
    "backspace": win32con.VK_BACK,
    "win": win32con.VK_LWIN,
    "enter": win32con.VK_RETURN,
    "esc": win32con.VK_ESCAPE,
    "space": win32con.VK_SPACE,
    "tab": win32con.VK_TAB,

    "up": win32con.VK_UP,
    "down": win32con.VK_DOWN,
    "left": win32con.VK_LEFT,
    "right": win32con.VK_RIGHT,

    "insert": win32con.VK_INSERT,
    "delete": win32con.VK_DELETE,
    "home": win32con.VK_HOME,
    "end": win32con.VK_END,
    "page_down": win32con.VK_NEXT,
    "page_up": win32con.VK_PRIOR,

    "f1": win32con.VK_F1,
    "f2": win32con.VK_F2,
    "f3": win32con.VK_F3,
    "f4": win32con.VK_F4,
    "f5": win32con.VK_F5,
    "f6": win32con.VK_F6,
    "f7": win32con.VK_F7,
    "f8": win32con.VK_F8,
    "f9": win32con.VK_F9,
    "f10": win32con.VK_F10,
    "f11": win32con.VK_F11,
    "f12": win32con.VK_F12
})

class KeyBoardInput (ctypes.Structure):
    _fields_ = [
        ("wVk",      wintypes.WORD),
        ("wScan",    wintypes.WORD),
        ("dwFlags",  wintypes.DWORD),
        ("time",     wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p)
    ]

class MouseInput (ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class HardwareInput (ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class InputUnion (ctypes.Union):
    _fields_ = [
        ("ki", KeyBoardInput),
        ("mi", MouseInput),
        ("hi", HardwareInput),
    ]

class Input (ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", InputUnion),
    ]

def send_input_tecla_api (codigo: int, pressionar: bool, unicode: bool) -> None:
    wVk = wScan = 0
    flags = 0 if pressionar else win32con.KEYEVENTF_KEYUP

    match unicode:
        # codepoint UTF-16
        case True:
            wScan = codigo
            flags |= win32con.KEYEVENTF_UNICODE
        # teclas especiais
        case False:
            wVk = codigo
            if codigo in CODIGOS_VK_TECLAS_EXTENDIDAS:
                flags |= win32con.KEYEVENTF_EXTENDEDKEY

    input = Input()
    input.type = win32con.INPUT_KEYBOARD
    input.union.ki = KeyBoardInput(wVk=wVk, wScan=wScan, dwFlags=flags, time=0, dwExtraInfo=0)

    send_input(1, ctypes.byref(input), ctypes.sizeof(Input))

def traduzir_tecla (tecla: str, virtual: bool = False) -> tuple[bool, list[int]]:
    """Traduzir a `tecla` para `(flag_unicode, [códigos])`
    - `virtual=True` para obter o código virtual do botão e não unicode"""
    assert tecla != "", "Tecla vazia é inválida"

    # teclas especiais
    if len(tecla) > 1:
        codigo = CODIGOS_VK_TECLAS.get(tecla)
        assert codigo is not None, f"Tecla '{tecla}' inválida"
        return False, [codigo]

    codepoint = ord(tecla)

    # letras e dígitos ascii com modificadores
    if virtual and codepoint <= 127:
        combo_vk_tecla: int = virtual_key_scan_w(tecla)
        codigo_vk_tecla: int = combo_vk_tecla & 0xFF
        modificadores: int = (combo_vk_tecla >> 8) & 0xFF

        codigos = list[int]()
        if modificadores & 1: codigos.append(win32con.VK_SHIFT)   # Shift
        if modificadores & 2: codigos.append(win32con.VK_CONTROL) # Ctrl
        if modificadores & 4: codigos.append(win32con.VK_MENU)    # Alt
        # AltGr
        if win32con.VK_MENU in codigos and win32con.VK_CONTROL in codigos:
            codigos.remove(win32con.VK_MENU)
            codigos.remove(win32con.VK_CONTROL)
            codigos.append(win32con.VK_RMENU)

        codigos.append(codigo_vk_tecla)
        return False, codigos

    # unicode até UTF-16
    if codepoint <= 0xFFFF:
        return True, [codepoint]

    # unicode com surrogate
    return True, [
        0xD800 + ((codepoint - 0x10000) >> 10),  # high
        0xDC00 + ((codepoint - 0x10000) & 0x3FF) # low
    ]

__all__ = [
    "traduzir_tecla",
    "send_input_tecla_api",
]