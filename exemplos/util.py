import bot

# Repetir a `condicao` por `timeout` segundos até que resulte em `True`
# Útil para se aguardar até que determinado evento aconteça
bot.util.aguardar_condicao(condicao=lambda: ..., timeout=5, delay=0.1)

"""
Funções para `str`
"""
bot.util.remover_acentuacao("")                 # Remover acentuações da string
bot.util.normalizar("")                         # Strip, lower, replace espaços por underline, remoção de acentuação e remoção de caracteres != a-zA-Z0-9_
bot.util.encontrar_texto("a", ("1", "2", "a"))  # Encontrar a melhor opção em opções onde igual ou parecido ao texto (Útil para OCR)

"""
Tempo
"""
bot.util.cronometro(resetar=False)  # Inicializa um cronômetro que retorna o tempo decorrido a cada chamada na função
bot.util.expandir_tempo(segundos=0) # Expandir a medida `segundos` para as duas primeiras unidades de grandeza (Hora, Minuto, Segundo ou Milissegundo)

"""
Decoradores de funções
"""
@bot.util.decoradores.timeout(segundos=30)                              # Executar a função por `segundos` até retornar ou `TimeoutError` caso ultrapasse o tempo
@bot.util.decoradores.retry(Exception, tentativas=5, segundos=0)        # Realizar `tentativas` de se chamar uma função após algum dos `erro` e aguardar `segundos` até tentar novamente
@bot.util.decoradores.prefixar_erro("Erro ao realizar XPTO")            # Adicionar um prefixo no erro caso a função resulte em exceção
@bot.util.decoradores.tempo_execucao                                    # Loggar o tempo de execução da função
@bot.util.decoradores.perfil_execucao                                   # Loggar o perfil de execução da função (DEV - Checar tempo de execução)
