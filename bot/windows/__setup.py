# std
import os
import shutil
import ctypes
# interno
from bot.util import normalizar
from bot.tipagem import caminho
from bot.estruturas import Diretorio, Coordenada
# externo
from pygetwindow import (
    Win32Window,
    getAllTitles as get_all_titles,
    getAllWindows as get_all_windows,
    getActiveWindow as get_active_window
)


def apagar_arquivo (caminho: caminho) -> None:
    """Apagar um arquivo"""
    if not caminho_existe(caminho): return
    assert confirmar_arquivo(caminho), "O caminho informado não é de um arquivo"
    os.remove(caminho)


def criar_pasta (caminho: caminho) -> caminho:
    """Criar pasta no `caminho` informado
    - Retorna o caminho absoluto da pasta criada"""
    os.mkdir(caminho)
    return caminho_absoluto(caminho)


def copiar_arquivo (de: caminho, para: caminho) -> caminho:
    """Copiar arquivo `de` um caminho `para` outro
    - Retorna o caminho para o qual foi copiado"""
    return caminho_absoluto(shutil.copyfile(de, para))


def extrair_nome_base (caminho: caminho) -> str:
    """Extrair a parte do nome e formato do `caminho`"""
    return os.path.basename(caminho)


def caminho_absoluto (caminho: caminho) -> caminho: 
    """Retorna a forma de caminho absoluto para o `caminho` informado"""
    return os.path.abspath(caminho)


def caminho_existe (caminho: caminho) -> bool:
    """Confirmar se `caminho` existe ou não"""
    return os.path.exists(caminho)


def confirmar_pasta (caminho: caminho) -> bool:
    """Confirmar se o `caminho` informado é de um diretório"""
    return os.path.isdir(caminho)


def confirmar_arquivo (caminho: caminho) -> bool:
    """Confirmar se o `caminho` informado é de um arquivo"""
    return os.path.isfile(caminho)


def cmd (comando: str) -> None:
    """Realizar um comando no `prompt`
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    os.system(comando)


def listar_diretorio (caminhoPasta: caminho) -> Diretorio:
    """Lista os caminhos dos arquivos e pastas do `caminhoPasta`"""
    assert caminho_existe(caminhoPasta), f"Caminho informado '{ caminhoPasta }' não existe"
    assert confirmar_pasta(caminhoPasta), f"Caminho informado '{ caminhoPasta }' não é de uma pasta"

    caminhoPasta = caminho_absoluto(caminhoPasta)
    diretorio = Diretorio(caminhoPasta, [], [])
    for item in os.listdir(caminhoPasta):
        caminho = f"{ caminhoPasta }\\{ item }"
        if confirmar_pasta(caminho): diretorio.pastas.append(caminho)
        elif confirmar_arquivo(caminho): diretorio.arquivos.append(caminho)

    return diretorio


def diretorio_execucao () -> Diretorio:
    """Obter informações do diretório de execução atual"""
    return listar_diretorio(os.getcwd())


class Janela:
    """Classe de interação com as janelas abertas. Abstração do pygetwindow
    - Alguns aplicativos pode não funcionar os métodos `self.focar()` e `self.minimizada`"""

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
        minimizada = self.minimizada
        if minimizada: ctypes.windll.user32.ShowWindow(self.janela._hWnd, 5)
        ctypes.windll.user32.SetForegroundWindow(self.janela._hWnd)
        if minimizada: self.restaurar()

    @staticmethod
    def titulos_janelas () -> list[str]:
        """Listar os titulos das janelas abertas
        - `@staticmethod`"""
        return sorted([ titulo for titulo in get_all_titles() if titulo != "" ])


__all__ = [
    "cmd",
    "Janela",
    "criar_pasta",
    "caminho_existe",
    "apagar_arquivo",
    "copiar_arquivo",
    "confirmar_pasta",
    "listar_diretorio",
    "caminho_absoluto",
    "confirmar_arquivo",
    "extrair_nome_base",
    "diretorio_execucao"
]
