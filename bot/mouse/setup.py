# std
from time import sleep
# interno
from .. import util, tipagem
from ..estruturas import Coordenada
# externo
import win32api, win32con
from pynput.mouse import Controller

MOUSE = Controller()
EVENTOS_MOUSE = {
    "left":   (win32con.MOUSEEVENTF_LEFTDOWN,   win32con.MOUSEEVENTF_LEFTUP),
    "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
    "right":  (win32con.MOUSEEVENTF_RIGHTDOWN,  win32con.MOUSEEVENTF_RIGHTUP)
}

def posicao_atual () -> tuple[int, int]:
    """Obter a posição `(x, y)` atual do mouse"""
    return win32api.GetCursorPos()

def posicao_central () -> tuple[int, int]:
    """Obter a posição `(x, y)` central da tela"""
    x, y = Coordenada.tela().transformar()
    return (x + 1, y + 1)

def transformar_posicao (coordenada: Coordenada | tuple[int, int] | None) -> tuple[int, int]:
    """Transformar a `coordenada` para posicao `(x, y)`"""
    match coordenada:
        case Coordenada():      return coordenada.transformar()
        case (int(), int()):    return coordenada
        case _:                 return posicao_atual()

def mover_mouse (coordenada: tuple[int, int] | Coordenada) -> None:
    """Mover o mouse, de forma instantânea, até a `coordenada`"""
    delay, coordenada = 0.025, transformar_posicao(coordenada)
    win32api.SetCursorPos(coordenada)
    sleep(delay)
    util.aguardar_condicao(lambda: posicao_atual() == coordenada, timeout=0.5, delay=delay)

def mover_mouse_deslizando (coordenada: tuple[int, int] | Coordenada) -> None:
    """Mover o mouse, deslizando pixel por pixel, até a `coordenada`"""
    posicao = transformar_posicao(coordenada)
    cronometro, tempo_limite = util.cronometro(), 5.0
    direcao_movimento = lambda n: 1 if n > 0 else -1 if n < 0 else 0
    movimento_relativo = lambda: tuple(desejado - atual for desejado, atual in zip(posicao, posicao_atual()))

    # mover enquanto diferente da coordenada desejada e dentro do tempo estipulado
    # se houver gargalo na máquina, a movimentação do mouse pode falhar
    while posicao_atual() != posicao and cronometro() < tempo_limite:
        x_relativo, y_relativo = movimento_relativo()
        while x_relativo or y_relativo:
            x_relativo -= (x := direcao_movimento(x_relativo))
            y_relativo -= (y := direcao_movimento(y_relativo))
            MOUSE.move(x, y)
            sleep(0.003)

def clicar_mouse (botao: tipagem.BOTOES_MOUSE = "left",
                  quantidade = 1,
                  coordenada: Coordenada | tuple[int, int] | None = None,
                  delay = 0.1) -> None:
    """Clicar com o `botão` do mouse `quantidade` vezes na `coordenada` ou posição atual
    - `delay` aplicado após 1 click"""
    assert quantidade >= 1, "Quantidade de clicks deve ser pelo menos 1"
    if coordenada: mover_mouse(coordenada)

    for _ in range(quantidade):
        for evento in EVENTOS_MOUSE[botao]:
            win32api.mouse_event(evento, 0, 0)
        sleep(delay)

def scroll_vertical (quantidade = 1,
                     direcao: tipagem.DIRECOES_SCROLL = "baixo",
                     coordenada: Coordenada | tuple[int, int] | None = None,
                     delay = 0.05) -> None:
    """Realizar o scroll vertical `quantidade` vezes para a `direcao` na `coordenada` ou posição atual
    - `delay` aplicado após 1 scroll"""
    assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"
    if coordenada: mover_mouse(coordenada)

    for _ in range(quantidade):
        MOUSE.scroll(0, -1 if direcao == "baixo" else 1)
        sleep(delay)

__all__ = [
    "Coordenada",
    "mover_mouse",
    "clicar_mouse",
    "posicao_atual",
    "posicao_central",
    "scroll_vertical",
    "mover_mouse_deslizando"
]