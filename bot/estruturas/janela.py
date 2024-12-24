# std
from __future__ import annotations
from typing import Self
import ctypes, warnings, logging
# interno
from . import Coordenada
from .. import util, tipagem
# externo
from pywinauto.timings import Timings
from pywinauto.win32structures import RECT
from pywinauto import Application, Desktop, mouse
from pywinauto.controls.hwndwrapper import HwndWrapper

# ignorar warnings do pywinauto
warnings.simplefilter('ignore', category=UserWarning)
# reduzir timeouts
Timings.after_setfocus_wait = 0.01
for nome in ("closeclick_retry", "window_find_retry", "after_clickinput_wait", "after_setcursorpos_wait"):
    setattr(Timings, nome, 0)
# desativar o mouse.move para não interfirir com o focar
mouse.move = lambda coords: None
# desativar forçadamente o logger do pywinauto
logger = logging.getLogger("pywinauto")
logger.disabled = True
for h in logger.handlers: h.close()
logger.handlers.clear()

class Janela:
    """Classe de interação com as janelas abertas. 
    - Abstração do `pywinauto`"""

    elemento: HwndWrapper
    """Elemento da janela"""
    aplicacao: Application
    """Application superior da janela"""

    def __init__ (self, titulo: str | None = None,
                        class_name: str | None = None,
                        backend: tipagem.BACKENDS_JANELA = "win32") -> None:
        """Inicializar a conexão com a janela
        - Se o `titulo` e `class_name` forem omitidos, será pego a janela focada atual
        - `backend` varia de acordo com a janela, testar com ambos para encontrar o melhor"""
        if not titulo and not class_name:
            handle = ctypes.windll.user32.GetForegroundWindow()
            self.elemento = Desktop(backend).window(handle=handle).wrapper_object()
            self.aplicacao = Application(backend).connect(handle=handle)
            return

        titulos_janelas = self.titulos_janelas()
        titulo_normalizado = util.normalizar(titulo or "")
        titulo = None if not titulo else titulo if titulo in titulos_janelas else ([
            titulo_janela
            for titulo_janela in titulos_janelas
            if titulo_normalizado in util.normalizar(titulo_janela)
        ] or [None])[0]

        args = { "title": titulo, "class_name": class_name, "visible_only": True }
        self.elemento = Desktop(backend).window(**args).wrapper_object()
        self.aplicacao = Application(backend).connect(**args)

    def __eq__ (self, other: Janela) -> bool:
        """Comparar se o handler de uma janela é o mesmo que a outra"""
        if not isinstance(other, Janela): return False
        return self.elemento.handle == other.elemento.handle
    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Janela '{self.titulo}'>"

    @property
    def titulo (self) -> str:
        """Titulo da janela"""
        return self.elemento.window_text()
    @property
    def maximizada (self) -> bool:
        """Checar se a janela está maximizada"""
        return self.elemento.is_maximized()
    @property
    def minimizada (self) -> bool:
        """Checar se a janela está minimizada"""
        return self.elemento.is_minimized()
    @property
    def focada (self) -> bool:
        """Checar se a janela está focada"""
        return self.elemento.is_active()
    @property
    def coordenada (self) -> Coordenada:
        """Coordenada da janela
        - `Coordenada` zerada caso a janela esteja minimizada"""
        box: RECT = self.elemento.rectangle()
        return Coordenada(box.left, box.top, box.width(), box.height())

    def minimizar (self) -> Self:
        """Minimizar janela"""
        self.elemento.minimize()
        return self
    def maximizar (self) -> Self:
        """Maximizar janela"""
        self.elemento.maximize()
        return self
    def restaurar (self) -> Self:
        """Restaurar a janela para o estado anterior"""
        self.elemento.restore()
        return self
    def focar (self) -> Self:
        """Focar na janela"""
        if self.minimizada: self.restaurar()
        self.elemento.set_focus()
        return self
    def fechar (self) -> None:
        """Fechar a janela atual"""
        self.elemento.close(5)
    def encerrar (self) -> None:
        """Encerrar o processo da aplicação forçadamente"""
        self.aplicacao.kill()

    def elementos (self, *, title: str = None, title_re: str = None,
                   class_name: str = None, class_name_re: str = None,
                   control_id: int = None, parent: HwndWrapper | None = None,
                   top_level_only=True, visible_only=True, enabled_only=True) -> list[HwndWrapper]:
        """Obter uma lista elementos com base nos parâmetros informados
        - Procura elementos a partir do nível superior da janela
        - O tipo do retorno pode ser diferente dependendo do tipo do backend e controle
        - Retornado uma classe genérica que compartilham múltiplos métodos"""
        return self.aplicacao.windows(title=title, title_re=title_re,
                                      class_name=class_name, class_name_re=class_name_re,
                                      control_id=control_id, parent=parent,
                                      top_level_only=top_level_only, visible_only=visible_only, enabled_only=enabled_only)

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