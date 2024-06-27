"""Módulo para realizar e tratar Logs
- Cria um LOG na raiz do projeto para fácil acesso `CAMINHO_LOG_ATUAL`
- Salva o LOG na pasta de persistência se requisitado `CAMINHO_LOG_PERSISTENCIA`
- Variáveis .ini `[logger] -> dias_persistencia, flag_persistencia, flag_debug`
    - `dias_persistencia` default: 14
    - `flag_persistencia` default: True
    - `flag_debug` default: False"""

from .__setup import *