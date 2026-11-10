# std
from time import sleep
from typing import Self
# interno
from .win_api import send_input_mouse_api, click_mouse_api
from bot import tipagem, tempo
from bot.estruturas import Coordenada
# externo
import win32api, win32con, win32gui

def transformar_posicao (coordenada: Coordenada | tuple[int, int] | None) -> tuple[int, int]:
    """Transformar a `coordenada` para posicao `(x, y)`"""
    match coordenada:
        case Coordenada(): return coordenada.centro()
        case (int(), int()): return coordenada
        case _: return Mouse.posicao_atual()

class Mouse:
    """Classe de controle do mouse
    - Alterar constantes `DELAY_...` para modificar tempo de espera após ação"""

    DELAY_CLICK  = 0.05
    DELAY_MOVER  = 0.05
    DELAY_SCROLL = 0.05
    DELAY_MOVER_RELATIVO = 0.001
    UMA_LINHA_SCROLL: int = 120

    def __repr__ (self) -> str:
        return "<bot.Mouse>"

    @staticmethod
    def posicao_atual () -> tuple[int, int]:
        """Obter a posição `(x, y)` atual do mouse"""
        return win32api.GetCursorPos()

    @staticmethod
    def posicao_central () -> tuple[int, int]:
        """Obter a posição `(x, y)` central da tela"""
        return Coordenada.Tela().centro()

    def mover (self, coordenada: tuple[int, int] | Coordenada) -> Self:
        """Mover o mouse, de forma instantânea, até a `coordenada`
        - `Coordenada()` posição central
        - `(int, int)` posição exata"""
        coordenada = transformar_posicao(coordenada)
        try: win32api.SetCursorPos(coordenada)
        except Exception: raise RuntimeError("Falha ao utilizar a API do Windows para movimentar o Mouse")

        sleep(self.DELAY_MOVER)
        tempo.aguardar(
            lambda: self.posicao_atual() == coordenada,
            timeout = 5,
            delay = self.DELAY_MOVER
        )
        return self

    def mover_relativo (self, x: int = 0, y: int = 0) -> Self:
        """Mover o mouse relativamente por `x` e `y` pixels
        - Positivo: `direita` e `baixo`
        - Negativo: `esquerda` e `cima`"""
        send_input_mouse_api(win32con.MOUSEEVENTF_MOVE, x, y)
        return self.sleep(self.DELAY_MOVER_RELATIVO)

    def mover_deslizando (self, coordenada: tuple[int, int] | Coordenada) -> Self:
        """Mover o mouse, pixel por pixel, até a `coordenada`
        - `Coordenada()` posição central
        - `(int, int)` posição exata"""
        cronometro = tempo.Cronometro()
        destino = transformar_posicao(coordenada)

        # Mover enquanto diferente da coordenada desejada e dentro do tempo estipulado
        while (atual := self.posicao_atual()) != destino and cronometro < 5.0:
            x, y = atual

            # Gerar próximo ponto com Bresenham
            dx = destino[0] - x
            dy = destino[1] - y
            erro = abs(dx) - abs(dy)
            erro2 = 2 * erro

            sx = 1 if dx > 0 else -1 if dx < 0 else 0
            if erro2 > -abs(dy):
                erro -= abs(dy)
                x += sx

            sy = 1 if dy > 0 else -1 if dy < 0 else 0
            if erro2 < abs(dx):
                erro += abs(dx)
                y += sy

            self.mover_relativo(x - atual[0], y - atual[1])

        return self.sleep(self.DELAY_MOVER)

    def clicar (self) -> Self:
        """Clicar com o botão esquerdo na posição atual"""
        click_mouse_api(self.DELAY_CLICK)
        return self

    def clicar_duplo (self) -> Self:
        """Clicar com o botão esquerdo 2 vezes na posição atual"""
        click_mouse_api(self.DELAY_CLICK, quantidade=2)
        return self

    def clicar_meio (self) -> Self:
        """Clicar com o botão do meio na posição atual"""
        click_mouse_api(self.DELAY_CLICK, botao="middle")
        return self

    def clicar_direito (self) -> Self:
        """Clicar com o botão direito na posição atual"""
        click_mouse_api(self.DELAY_CLICK, botao="right")
        return self

    def scroll (self, quantidade: int = 1) -> Self:
        """Realizar o scroll vertical `quantidade` vezes para baixo na posição atual"""
        assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"

        for _ in range(quantidade):
            send_input_mouse_api(win32con.MOUSEEVENTF_WHEEL, mouse_data=-self.UMA_LINHA_SCROLL)
            sleep(self.DELAY_SCROLL)

        return self

    def scroll_up (self, quantidade: int = 1) -> Self:
        """Realizar o scroll vertical `quantidade` vezes para cima na posição atual"""
        assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"

        for _ in range(quantidade):
            send_input_mouse_api(win32con.MOUSEEVENTF_WHEEL, mouse_data=self.UMA_LINHA_SCROLL)
            sleep(self.DELAY_SCROLL)

        return self

    def sleep (self, segundos: int | float = 1) -> Self:
        """Aguardar por `segundos` até continuar a execução"""
        sleep(segundos)
        return self

    def rgb (self) -> tipagem.rgb:
        """Obter a cor `(R, G, B)` do pixel na posição atual do mouse"""
        device_context: int = 0
        try:
            device_context = win32gui.GetDC(0)
            x, y = self.posicao_atual()
            pixel = win32gui.GetPixel(device_context, x, y)
            return (
                pixel & 0xff,
                (pixel >> 8) & 0xff,
                (pixel >> 16) & 0xff,
            )
        finally:
            if device_context:
                win32gui.ReleaseDC(0, device_context)

mouse = Mouse()
"""Classe de controle do mouse
- Alterar constantes `DELAY_...` para modificar tempo de espera após ação"""

__all__ = ["mouse"]