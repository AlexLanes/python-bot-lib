# std
from time import sleep
# interno
import bot
from bot.estruturas import Coordenada
# externo
from pyscreeze import pixel
from pynput.mouse import Controller, Button
from win32api import (
    GetCursorPos as get_cursor_position, 
    SetCursorPos as set_cursor_position
)

MOUSE = Controller()

def posicao_mouse () -> tuple[int, int]:
    """Obter a posição (X, Y) do mouse"""
    return get_cursor_position()

def obter_x_y (coordenada: tuple[int, int] | Coordenada | None) -> tuple[int, int]:
    """Obter posicao (x, y) do item recebido
    - `Default` posicao_mouse()"""
    c = coordenada # apelido
    if isinstance(c, Coordenada): return c.transformar() # centro da coordenada
    if isinstance(c, tuple) and len(c) == 2: return c
    return posicao_mouse()

def mover_mouse (coordenada: tuple[int, int] | Coordenada) -> None:
    """Mover o mouse até a `coordenada`"""
    coordenada = obter_x_y(coordenada)
    # mover
    set_cursor_position(coordenada)
    MOUSE.position = coordenada
    # esperar atualizar
    sleep(0.01)
    c = coordenada
    bot.util.aguardar_condicao(lambda: c == MOUSE.position and c == get_cursor_position(), 0.1, 0.002)

def clicar_mouse (botao: bot.tipagem.BOTOES_MOUSE = "left",
                  quantidade=1,
                  coordenada: Coordenada | tuple[int, int] = None,
                  delay=0.1) -> None:
    """Clicar com o `botão` do mouse `quantidade` vezes na `coordenada` ou posição atual"""
    if coordenada: mover_mouse(coordenada) # mover mouse se requisitado
    MOUSE.click(Button[botao], max(1, quantidade))
    sleep(delay)

def scroll_vertical (quantidade=1,
                     direcao: bot.tipagem.DIRECOES_SCROLL = "baixo",
                     coordenada: Coordenada | tuple[int, int] = None,
                     delay=0.05) -> None:
    """Realizar o scroll vertical `quantidade` vezes para a `direcao` na `coordenada` ou posição atual"""
    quantidade = max(1, quantidade)
    if coordenada: mover_mouse(coordenada) # mover mouse se requisitado
    for _ in range(quantidade):
        MOUSE.scroll(0, -1 if direcao == "baixo" else 1)
        sleep(delay)

def cor_mouse () -> bot.tipagem.rgb:
    """Obter o RGB da posição atual do mouse
    - `r, g, b = cor_mouse()`"""
    return pixel(*posicao_mouse())

__all__ = [
    "cor_mouse",
    "Coordenada",
    "mover_mouse",
    "clicar_mouse",
    "posicao_mouse",
    "scroll_vertical"
]
