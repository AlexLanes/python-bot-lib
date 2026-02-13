"""Biblioteca com funcionalidades gerais para criação de automações para o Windows"""

# Não pode ser usado internamente importando relativamente
from bot.configfile.setup import configfile
from bot.logger.setup     import logger
from bot.mouse.setup      import mouse
from bot.teclado.setup    import teclado

from bot import (
    tipagem,
    util,
    sistema,
    estruturas,

    argumentos,
    database,
    email,
    formatos,
    ftp,
    http,
    imagem,
    navegador,
    tempo,
    video
)