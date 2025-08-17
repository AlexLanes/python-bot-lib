"""Biblioteca com funcionalidades gerais para criação de automações para o Windows"""

# Não pode ser usado internamente importando relativamente
from bot.logger  import logger
from bot.mouse   import mouse
from bot.teclado import teclado

from . import (
    tipagem,
    util,
    sistema,
    estruturas,
    configfile,

    argumentos,
    database,
    email,
    formatos,
    ftp,
    http,
    imagem,
    navegador,
    video
)