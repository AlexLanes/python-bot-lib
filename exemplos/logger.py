import bot

"""
LOG
Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_persistencia: True, flag_debug: False]`

Log formatado e criado automaticamente para
    stdout
    arquivo `.log` na raiz da execução
    arquivo log no diretório `/log` (Pode ser desativado via configfile)
"""
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
bot.logger.informar("Antes")
bot.logger.linha_horizontal()
bot.logger.informar("Depois")

# Obter caminho dos LOGs
bot.logger.caminho_log_raiz()           # Caminho para o log da raiz `.log`
bot.logger.caminho_log_persistencia()   # Caminho para o log no diretório `/log` (Ativo por padrão no configfile)

# Limpar o `caminho_log_raiz()` não afeta o `caminho_log_persistencia()`
bot.logger.limpar_log_raiz()
