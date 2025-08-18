# std
from time import sleep
from typing import Self
# interno
from .win_api import send_input_mouse_api
import bot
from bot.estruturas import Coordenada
# externo
import win32api, win32con

def transformar_posicao (coordenada: Coordenada | tuple[int, int] | None) -> tuple[int, int]:
    """Transformar a `coordenada` para posicao `(x, y)`"""
    match coordenada:
        case Coordenada(): return coordenada.transformar()
        case (int(), int()): return coordenada
        case _: return Mouse.posicao_atual()

class Mouse:
    """Classe de controle do mouse
    - Alterar constantes `DELAY_...` para modificar tempo de espera após ação"""

    DELAY_CLICK = 0.1
    DELAY_MOVER = 0.1
    DELAY_SCROLL = 0.05
    DELAY_MOVER_RELATIVO = 0.001

    UMA_LINHA_SCROLL: int = 120
    EVENTOS_BOTOES = {
        "left":   (win32con.MOUSEEVENTF_LEFTDOWN,   win32con.MOUSEEVENTF_LEFTUP),
        "middle": (win32con.MOUSEEVENTF_MIDDLEDOWN, win32con.MOUSEEVENTF_MIDDLEUP),
        "right":  (win32con.MOUSEEVENTF_RIGHTDOWN,  win32con.MOUSEEVENTF_RIGHTUP)
    }

    def __repr__ (self) -> str:
        return "<bot.Mouse>"

    @staticmethod
    def posicao_atual () -> tuple[int, int]:
        """Obter a posição `(x, y)` atual do mouse"""
        return win32api.GetCursorPos()

    @staticmethod
    def posicao_central () -> tuple[int, int]:
        """Obter a posição `(x, y)` central da tela"""
        return Coordenada.tela().transformar()

    def mover (self, coordenada: tuple[int, int] | Coordenada) -> Self:
        """Mover o mouse, de forma instantânea, até a `coordenada`"""
        coordenada = transformar_posicao(coordenada)
        win32api.SetCursorPos(coordenada)
        sleep(self.DELAY_MOVER)
        bot.util.aguardar_condicao(
            lambda: self.posicao_atual() == coordenada,
            timeout = 0.5
        )
        return self

    def mover_relativo (self, x: int = 0, y: int = 0) -> Self:
        """Mover o mouse relativamente por `x` e `y` pixels
        - Positivo: `direita` e `baixo`
        - Negativo: `esquerda` e `cima`"""
        send_input_mouse_api(win32con.MOUSEEVENTF_MOVE, x, y)
        sleep(self.DELAY_MOVER_RELATIVO)
        return self

    def mover_deslizando (self, coordenada: tuple[int, int] | Coordenada) -> Self:
        """Mover o mouse, pixel por pixel, até a `coordenada`"""
        posicao = transformar_posicao(coordenada)
        cronometro, tempo_limite = bot.util.Cronometro(), 5.0
        direcao_movimento = lambda n: 1 if n > 0 else -1 if n < 0 else 0
        movimento_relativo = lambda: tuple(desejado - atual for desejado, atual in zip(posicao, self.posicao_atual()))

        # mover enquanto diferente da coordenada desejada e dentro do tempo estipulado
        # se houver gargalo na máquina, a movimentação do mouse pode falhar
        while self.posicao_atual() != posicao and cronometro() < tempo_limite:
            x_relativo, y_relativo = movimento_relativo()
            while x_relativo or y_relativo:
                x_relativo -= (x := direcao_movimento(x_relativo))
                y_relativo -= (y := direcao_movimento(y_relativo))
                self.mover_relativo(x, y)

        sleep(self.DELAY_MOVER)
        return self

    def clicar (self, quantidade = 1, botao: bot.tipagem.BOTOES_MOUSE = "left") -> Self:
        """Clicar com o `botão` do mouse `quantidade` vezes na posição atual"""
        assert quantidade >= 1, "Quantidade de clicks deve ser pelo menos 1"

        for _ in range(quantidade):
            for evento in self.EVENTOS_BOTOES[botao]:
                send_input_mouse_api(evento)
            sleep(self.DELAY_CLICK)

        return self

    def scroll_vertical (self, quantidade = 1, direcao: bot.tipagem.DIRECOES_SCROLL = "baixo") -> Self:
        """Realizar o scroll vertical `quantidade` vezes para a `direcao` na posição atual"""
        assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"

        um_scroll = -self.UMA_LINHA_SCROLL if direcao == "baixo" else self.UMA_LINHA_SCROLL
        for _ in range(quantidade):
            send_input_mouse_api(win32con.MOUSEEVENTF_WHEEL, mouse_data=um_scroll)
            sleep(self.DELAY_SCROLL)

        return self

mouse = Mouse()
"""Classe de controle do mouse
- Alterar constantes `DELAY_...` para modificar tempo de espera após ação"""

__all__ = ["mouse"]