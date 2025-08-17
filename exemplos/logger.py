import bot

"""
LOG
Classe configurada para criar, consultar e tratar os arquivos de log.  
Possível alterar configurações mudando as constantes antes do logger ser inicializado
#### Deve ser inicializado `bot.logger.inicializar_logger()`

- Stream para o `stdout`
- Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
- Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
- Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False]`
"""
bot.logger.inicializar_logger()
bot.logger.debug("mensagem")    # Log nível 'DEBUG' (Desativado por padrão no configfile)
bot.logger.informar("mensagem") # Log nível 'INFO'
bot.logger.alertar("mensagem")  # Log nível 'WARNING'
# Log nível 'ERROR'. Exceção capturada automaticamente dentro do `except`
try: a = 1 / 0
except ZeroDivisionError: bot.logger.erro("mensagem")
# Log nível 'ERROR'. Exceção informada manualmente
erro = Exception("xpto")
bot.logger.erro("mensagem", excecao=erro)

# Adicionar uma linha horizontal para separar seções visualmente
bot.logger.informar("Antes")\
          .linha_horizontal()\
          .informar("Depois")

# Obter caminho dos LOGs
bot.logger.CAMINHO_LOG_RAIZ         # Caminho para o log da raiz `.log`
bot.logger.CAMINHO_LOG_PERSISTENCIA # Caminho para o log no diretório `/log`

# Limpar o `CAMINHO_LOG_RAIZ` não afeta o `CAMINHO_LOG_PERSISTENCIA`
bot.logger.limpar_log_raiz()