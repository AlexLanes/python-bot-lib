# std
from time import sleep
# interno
from .. import util, tipagem
from ..estruturas import Coordenada
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
    """Mover o mouse, de forma instantanea, até a `coordenada`"""
    coordenada = obter_x_y(coordenada)
    # mover
    set_cursor_position(coordenada)
    MOUSE.position = coordenada
    # esperar atualizar
    sleep(0.01)
    c = coordenada
    util.aguardar_condicao(lambda: c == MOUSE.position and c == get_cursor_position(), 0.1, 0.002)

def mover_mouse_deslizando (coordenada: tuple[int, int] | Coordenada) -> None:
    """Mover o mouse, deslizando pixel por pixel, até a `coordenada`"""
    coordenada = obter_x_y(coordenada)
    cronometro, tempo_limite = util.cronometro(), 5.0
    direcao_movimento = lambda n: 1 if n > 0 else -1 if n < 0 else 0
    movimento_relativo = lambda: tuple(desejado - atual for desejado, atual in zip(coordenada, posicao_mouse()))
    # mover enquanto diferente da coordenada desejada e dentro do tempo estipulado
    # se houver gargalo na máquina, a movimentação do mouse pode falhar
    while posicao_mouse() != coordenada and cronometro() < tempo_limite:
        x_relativo, y_relativo = movimento_relativo()
        while x_relativo or y_relativo:
            x_relativo -= (x := direcao_movimento(x_relativo))
            y_relativo -= (y := direcao_movimento(y_relativo))
            MOUSE.move(x, y)
            sleep(0.001)

def clicar_mouse (botao: tipagem.BOTOES_MOUSE = "left",
                  quantidade=1,
                  coordenada: Coordenada | tuple[int, int] = None,
                  delay=0.1) -> None:
    """Clicar com o `botão` do mouse `quantidade` vezes na `coordenada` ou posição atual"""
    if coordenada: mover_mouse(coordenada) # mover mouse se requisitado
    MOUSE.click(Button[botao], max(1, quantidade))
    sleep(delay)

def scroll_vertical (quantidade=1,
                     direcao: tipagem.DIRECOES_SCROLL = "baixo",
                     coordenada: Coordenada | tuple[int, int] = None,
                     delay=0.05) -> None:
    """Realizar o scroll vertical `quantidade` vezes para a `direcao` na `coordenada` ou posição atual"""
    quantidade = max(1, quantidade)
    if coordenada: mover_mouse(coordenada) # mover mouse se requisitado
    for _ in range(quantidade):
        MOUSE.scroll(0, -1 if direcao == "baixo" else 1)
        sleep(delay)

def cor_mouse () -> tipagem.rgb:
    """Obter o RGB da posição atual do mouse
    - `r, g, b = cor_mouse()`"""
    return pixel(*posicao_mouse())

__all__ = [
    "cor_mouse",
    "Coordenada",
    "mover_mouse",
    "clicar_mouse",
    "posicao_mouse",
    "scroll_vertical",
    "mover_mouse_deslizando"
]
