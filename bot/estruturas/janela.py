# std
from __future__ import annotations
from typing import Self
import ctypes, warnings, logging
# interno
from . import Coordenada
from .. import util, tipagem
# externo
from pywinauto.timings import Timings
from pywinauto import Application, Desktop
from pywinauto.controls.hwndwrapper import HwndWrapper

# ignorar warnings do pywinauto
warnings.simplefilter('ignore', category=UserWarning)
# reduzir o timeouts
Timings.closeclick_retry = 0
Timings.window_find_retry = 0
Timings.after_setfocus_wait = 0
Timings.after_clickinput_wait = 0
Timings.after_setcursorpos_wait = 0
# desativar forçadamente o logger do pywinauto
logger = logging.getLogger("pywinauto")
logger.disabled = True
for h in logger.handlers: h.close()
logger.handlers.clear()

class Janela:
    """Classe de interação com as janelas abertas. 
    - Abstração do `pywinauto`"""

    __janela: HwndWrapper
    """Conexão com a janela superior"""
    __aplicacao: Application
    """Application da janela"""

    def __init__ (self, titulo: str = None,
                        class_name: str = None,
                        backend: tipagem.BACKENDS_JANELA = "win32") -> None:
        """Inicializar a conexão com a janela
        - Se o `titulo` e `class_name` forem omitidos, será pego a janela focada atual
        - `backend` varia de acordo com a janela, testar com ambos para encontrar o melhor"""
        if not titulo and not class_name:
            handle = ctypes.windll.user32.GetForegroundWindow()
            self.__janela = Desktop(backend).window(handle=handle)
            self.__aplicacao = Application(backend).connect(handle=handle)
            return

        titulos_janelas = self.titulos_janelas()
        titulo_normalizado = util.normalizar(titulo)
        titulos = [titulo] if titulo in titulos_janelas else [
            titulo
            for titulo in titulos_janelas
            if titulo_normalizado in util.normalizar(titulo)
        ]
        assert titulos, f"Janela de titulo '{titulo}' não foi encontrada"

        self.__janela = Desktop(backend).window(title=titulos[0], class_name=class_name, visible_only=True)
        self.__aplicacao = Application(backend).connect(title=titulos[0], class_name=class_name, visible_only=True)

    def __eq__ (self, other: Janela) -> bool:
        """Comparar se o handler de uma janela é o mesmo que a outra"""
        if not isinstance(other, Janela): return False
        return self.__janela.handle == other.__janela.handle

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Janela '{self.titulo}'>"

    @property
    def titulo (self) -> str:
        """Titulo da janela"""
        return self.__janela.window_text()
    @property
    def maximizada (self) -> bool:
        """Checar se a janela está maximizada"""
        return self.__janela.is_maximized()
    @property
    def minimizada (self) -> bool:
        """Checar se a janela está minimizada"""
        return self.__janela.is_minimized()
    @property
    def focada (self) -> bool:
        """Checar se a janela está focada"""
        return self.__janela.is_active()
    @property
    def coordenada (self) -> Coordenada:
        """Coordenada da janela
        - `Coordenada` zerada caso a janela esteja minimizada"""
        box = self.__janela.rectangle()
        return Coordenada(box.left, box.top, box.width(), box.height())

    def minimizar (self) -> Self:
        """Minimizar janela"""
        self.__janela.minimize()
        return self
    def maximizar (self) -> Self:
        """Maximizar janela"""
        self.__janela.maximize()
        return self
    def restaurar (self) -> Self:
        """Restaurar a janela para o estado anterior"""
        self.__janela.restore()
        return self
    def focar (self) -> Self:
        """Focar na janela"""
        if self.minimizada: self.restaurar()
        self.__janela.set_focus()
        return self
    def fechar (self) -> None:
        """Fechar janela"""
        self.__aplicacao.kill()

    def elementos (self, *, title: str = None, title_re: str = None,
                   class_name: str = None, control_id: int = None,
                   top_level_only=True, visible_only=True, enabled_only=True) -> list[HwndWrapper]:
        """Obter uma lista elementos com base nos parâmetros informados
        - O tipo do retorno pode ser diferente dependendo do tipo do backend e controle
        - Retornado uma classe genérica que compartilham múltiplos métodos"""
        return self.__aplicacao.windows(title=title, title_re=title_re, class_name=class_name,
                                        control_id=control_id, top_level_only=top_level_only,
                                        visible_only=visible_only, enabled_only=enabled_only)

    @staticmethod
    def titulos_janelas () -> set[str]:
        """Listar os titulos das janelas abertas
        - `@staticmethod`"""
        janelas: list[HwndWrapper] = Desktop().windows(visible_only=True)
        return {
            titulo
            for janela in janelas
            if (titulo := janela.window_text())
        }

__all__ = ["Janela"]
