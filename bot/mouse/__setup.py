# interno
import bot
from bot.tipagem import Coordenada
# externo
from pynput.mouse import Controller


mouse = Controller()


def obter_x_y (coordenada: tuple[int, int] | Coordenada) -> tuple[int, int] | tuple[None, None]:
    """Obter coordenada (x, y) do item recebido"""
    if isinstance(coordenada, Coordenada): return coordenada.transformar()
    if isinstance(coordenada, tuple): return coordenada
    return (None, None)


def posicao_mouse () -> tuple[int, int]:
    """Obter a posição (X, Y) do mouse"""
    return tuple(bot.pyautogui.position())


def mover_mouse (coordenada: tuple[int, int] | Coordenada) -> None:
    """Mover o mouse até as cordenadas"""
    x, y = obter_x_y(coordenada)
    bot.pyautogui.moveTo(x, y)


def clicar_mouse (coordenada: Coordenada | tuple[int, int] = None, botao: bot.tipagem.BOTOES_MOUSE = "left", quantidade=1) -> None:
    """Clicar com o `botão` do mouse na `coordenada` `quantidade` vezes
    - Default `Coordenada` posição atual do mouse
    - Default `botao` botão esquerdo do mouse
    - Default `quantidade` 1"""
    x, y = obter_x_y(coordenada)
    bot.pyautogui.click(x, y, quantidade, 0.1, botao)


def scroll_vertical (quantidade: int, direcao: bot.tipagem.DIRECOES_SCROLL = "baixo") -> None:
    """Realizar o scroll vertical na posição atual do mouse"""
    mouse.scroll(0, -quantidade if direcao == "baixo" else quantidade)


def rgb_mouse () -> bot.tipagem.FrequenciaCor:
    """Obter o RGB da coordenada atual do mouse"""
    rgb = bot.pyautogui.pixel(*bot.pyautogui.position())
    return bot.tipagem.FrequenciaCor(1, rgb)


__all__ = [
    "rgb_mouse",
    "mover_mouse",
    "clicar_mouse",
    "posicao_mouse",
    "scroll_vertical"
]
