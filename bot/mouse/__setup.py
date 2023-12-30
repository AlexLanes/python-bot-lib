# interno
import bot
from bot.tipagem import Coordenada
# externo
from pyscreeze import pixel
from pynput.mouse import Controller, Button


mouse = Controller()


def posicao_mouse () -> tuple[int, int]:
    """Obter a posição (X, Y) do mouse"""
    return mouse.position


def obter_x_y (coordenada: tuple[int, int] | Coordenada | None) -> tuple[int, int]:
    """Obter posicao (x, y) do item recebido
    - `Default` posicao_mouse()"""
    c = coordenada # apelido
    if isinstance(c, Coordenada): return c.transformar() # centro da coordenada
    if isinstance(c, tuple) and len(c) >= 2: return (c[0], c[1])
    return posicao_mouse()


def mover_mouse (coordenada: tuple[int, int] | Coordenada) -> None:
    """Mover o mouse até as cordenadas"""
    mouse.position = obter_x_y(coordenada)


def clicar_mouse (coordenada: Coordenada | tuple[int, int] = None, botao: bot.tipagem.BOTOES_MOUSE = "left", quantidade=1) -> None:
    """Clicar com o `botão` do mouse na `coordenada` `quantidade` vezes
    - Default `Coordenada` posição atual do mouse
    - Default `botao` botão esquerdo do mouse
    - Default `quantidade` 1"""
    if coordenada: mover_mouse(coordenada) # mover mouse se requisitado
    botao: int = Button.right if botao == "right" else Button.middle if botao == "middle" else Button.left # Enum do botão
    mouse.click(botao, max(1, quantidade)) # clicar


def scroll_vertical (quantidade: int, direcao: bot.tipagem.DIRECOES_SCROLL = "baixo") -> None:
    """Realizar o scroll vertical na posição atual do mouse"""
    mouse.scroll(0, -quantidade if direcao == "baixo" else quantidade)


def rgb_mouse () -> tuple[int, int, int]:
    """Obter o RGB da posição atual do mouse
    - `r, g, b = rgb_mouse()`"""
    return pixel(*posicao_mouse())


__all__ = [
    "rgb_mouse",
    "mover_mouse",
    "clicar_mouse",
    "posicao_mouse",
    "scroll_vertical"
]
