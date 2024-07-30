"""Módulo para realizar e tratar Logs
- Cria um LOG na raiz do projeto para fácil acesso `caminho_log_atual()`
- Salva o LOG na pasta de persistência se requisitado `caminho_log_persistencia()`
- Caso o `bot.configurar_diretorio()` não tenha sido utilizado, o diretório de execução será utilizado
- Variáveis .ini `[logger] -> dias_persistencia, flag_persistencia, flag_debug`
    - `dias_persistencia` default: 14
    - `flag_persistencia` default: True
    - `flag_debug` default: False"""

from .__setup import *