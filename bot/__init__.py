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
from . import sistema
from . import teclado
from . import tipagem
from . import util

def configurar_diretorio (caminho: str | estruturas.Caminho) -> None:
    """Configurar o diretório de execução do bot manualmente
    - `configfile` e `logger` utilizam para localizarem o diretório de execução"""
    caminho = estruturas.Caminho(str(caminho))
    diretorio = caminho.parente if caminho.arquivo() else caminho
    from bot.configfile.setup import inicializar_configfile
    inicializar_configfile()
    from bot.logger.setup import inicializar_logger
    inicializar_logger(diretorio)
