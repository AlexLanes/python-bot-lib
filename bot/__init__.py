"""Biblioteca com funcionalidades gerais para criação de automações para o Windows"""

from . import tipagem, util, estruturas

from bot.mouse import *
from bot.teclado import *
from . import sistema

from . import argumentos
from . import configfile
from . import database
from . import email
from . import formatos
from . import ftp
from . import http
from . import imagem
from . import logger
from . import navegador
from . import video

def configurar_diretorio (caminho: str | sistema.Caminho) -> None:
    """Configurar o diretório de execução do bot manualmente
    - `configfile` e `logger` utilizam para localizarem o diretório de execução"""
    caminho = sistema.Caminho(str(caminho))
    diretorio = caminho.parente if caminho.arquivo() else caminho
    from bot.configfile.setup import inicializar_configfile
    inicializar_configfile()
    from bot.logger.setup import inicializar_logger
    inicializar_logger(diretorio)
