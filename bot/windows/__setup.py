# std
from shutil import copy as copiar_arquivo
from os import (
    path,
    system,
    getcwd as get_cwd,
    listdir as list_dir,
    mkdir as criar_pasta,
    remove as apagar_arquivo
)
# interno
from bot.util import normalizar
from bot.tipagem import Diretorio, Coordenada, caminho
# externo
from pywinauto.application import Application
from pygetwindow import (
    Win32Window,
    getAllTitles as get_all_titles,
    getAllWindows as get_all_windows,
    getActiveWindow as get_active_window
)


def cmd (comando: str) -> None | Exception:
    """Realizar um comando no `prompt`
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    system(comando)


def listar_diretorio (caminhoPasta: caminho) -> Diretorio:
    """Lista os caminhos dos arquivos e pastas do `caminhoPasta`"""
    assert path.exists(caminhoPasta), f"Caminho informado '{ caminhoPasta }' não existe"
    assert path.isdir(caminhoPasta), f"Caminho informado '{ caminhoPasta }' não é de uma pasta"

    caminhoPasta = path.abspath(caminhoPasta)
    diretorio = Diretorio(caminhoPasta, [], [])
    for item in list_dir(caminhoPasta):
        caminho = f"{ caminhoPasta }\\{ item }"
        if path.isdir(caminho): diretorio.pastas.append(caminho)
        elif path.isfile(caminho): diretorio.arquivos.append(caminho)

    return diretorio


def diretorio_execucao () -> Diretorio:
    """Obter informações do diretório de execução atual"""
    return listar_diretorio(get_cwd())


class Janela:
    """Classe de interação com as janelas abertas. Abstração do pygetwindow"""

    janela: Win32Window
    """Handler da janela"""

    def __init__ (self, titulo: str = None) -> None:
        """Inicializar o handler da janela com o primeiro titulo encontrado
        - Se o `titulo` for omitido, será pego a janela focada atual"""
        janelas: list[Win32Window] = [w for w in get_all_windows()
                                      if titulo != None and normalizar(titulo) in normalizar(w.title)]
        self.janela = janelas[0] if len(janelas) else get_active_window()

    def __eq__ (self, other) -> bool:
        """Comparar se o handler de uma janela é o mesmo que a outra"""
        return self.janela == other.janela

    @property
    def titulo (self) -> str:
        """Titulo da janela"""
        return self.janela.title
    @property
    def maximizada (self) -> bool:
        """Checar se a janela está maximizada"""
        return self.janela.isMaximized
    @property
    def minimizada (self) -> bool:
        """Checar se a janela está minimizada"""
        return self.janela.isMinimized
    @property
    def focada (self) -> bool:
        """Checar se a janela está focada"""
        return self.janela.isActive
    @property
    def coordenada (self) -> Coordenada:
        """Coordenada da janela"""
        box = self.janela.box
        return Coordenada(box.left, box.top, box.width, box.height)
    
    def minimizar (self) -> None:
        """Minimizar janela"""
        self.janela.minimize()
    def maximizar (self) -> None:
        """Maximizar janela"""
        self.janela.maximize()
    def fechar (self) -> None:
        """Fechar janela"""
        self.janela.close()
    def restaurar (self) -> None:
        """Restaurar a janela para o tamanho normal"""
        self.janela.restore()
    def focar (self) -> None:
        """Focar a janela"""
        if self.focada: return
        Application().connect(handle=self.janela._hWnd).top_window().set_focus()
        self.restaurar()


def titulos_janelas () -> list[str]:
    """Listar os titulos das janelas abertas"""
    return sorted([ titulo for titulo in get_all_titles() if titulo != "" ])


__all__ = [
    "cmd",
    "path",
    "Janela",
    "criar_pasta",
    "apagar_arquivo",
    "copiar_arquivo",
    "titulos_janelas",
    "listar_diretorio",
    "diretorio_execucao"
]
