# std
from time import sleep
from typing import Literal
# interno
import bot
from bot.estruturas import Coordenada
# externo
from pyscreeze import pixel
from pynput.mouse import Controller, Button
from win32gui import GetCursorInfo as get_cursor_info


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


def mover_mouse (coordenada: tuple[int, int] | Coordenada, delay=0.0) -> None:
    """Mover o mouse até a `coordenada`
    - `delay` é necessário para aguardar atualizar o tipo do ponteiro"""
    delay /= 2
    mouse.position = obter_x_y(coordenada)
    # atualizar o ponteiro
    mouse.move(1, -1); sleep(delay)
    mouse.move(-1, 1); sleep(delay)


def clicar_mouse (coordenada: Coordenada | tuple[int, int] = None, 
                  botao: bot.tipagem.BOTOES_MOUSE = "left", 
                  quantidade=1, delay=0.5) -> None:
    """Clicar com o `botão` do mouse na `coordenada` `quantidade` vezes
    - Default `coordenada`: posição atual do mouse"""
    if coordenada: mover_mouse(coordenada) # mover mouse se requisitado
    botao: Button = Button[botao] # Enum do botão
    mouse.click(botao, max(1, quantidade)) # clicar
    sleep(delay)


def scroll_vertical (quantidade: int, direcao: bot.tipagem.DIRECOES_SCROLL = "baixo", delay=0.02) -> None:
    """Realizar o scroll vertical na posição atual do mouse `quantidade` vezes na `direcao` informada"""
    quantidade = max(1, quantidade)
    for _ in range(quantidade):
        mouse.scroll(0, -1 if direcao == "baixo" else 1)
        sleep(delay)


def cor_mouse () -> tuple[int, int, int]:
    """Obter o RGB da posição atual do mouse
    - `r, g, b = obter_rgb_mouse()`"""
    return pixel(*posicao_mouse())


def tipo_ponteiro () -> Literal["normal", "clicavel", "texto", "indefinido"]:
    """Obter o tipo do ponteiro atual do mouse"""
    return { 65541: "texto", 65539: "normal", 65567: "clicavel" } \
        .get(get_cursor_info()[1], "indefinido")


__all__ = [
    "cor_mouse",
    "mover_mouse",
    "clicar_mouse",
    "tipo_ponteiro",
    "posicao_mouse",
    "scroll_vertical"
]
