import bot

"""
Pressionar teclado
"""
# Apertar e soltar uma tecla qtd vezes
bot.teclado.apertar_tecla(tecla="", quantidade=1, delay=0.1)

# Digitar o texto pressionando cada tecla do texto e soltando em seguida
bot.teclado.digitar_teclado("", delay=0.05)

# Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa
bot.teclado.atalho_teclado([], delay=0.5)


"""
Observar teclado
"""
# Observar quando a tecla é apertada e chamar o callback
bot.teclado.observar_tecla("enter", lambda: print("enter apertado"))
