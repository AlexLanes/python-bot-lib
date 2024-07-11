"""Pacote com funcionalidades gerais para criação de Bots"""

from . import argumentos
from . import configfile
from . import database
from . import email
from . import estruturas
from . import formatos
from . import ftp
from . import http
from . import imagem
from . import logger
from . import mouse
from . import navegador
from . import teclado
from . import tipagem
from . import util
from . import windows

def configurar_diretorio (caminho: tipagem.caminho) -> None:
    """Configurar o diretório de execução do bot manualmente
    - Informar o `caminho` para o diretório ou apenas o `__file__` do main.py
    - `configfile` e `logger` utilizam para localizarem o diretório de execução"""
    diretorio = caminho if windows.afirmar_diretorio(caminho) else windows.nome_diretorio(caminho)
    configfile.__setup.DIRETORIO_EXECUCAO = diretorio
    logger.__setup.DIRETORIO_EXECUCAO = diretorio
