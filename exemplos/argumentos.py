import bot

"""
Supondo que o Python tenha sido executado com os seguintes argumentos
python argumentos.py posicional "outro posicional" --nome Alex --idade "28 anos"
"""

# Checar se argumentos nomeados existem
bot.argumentos.nomeado_existe("nome") # True
bot.argumentos.nomeado_existe("não_existente") # False

# Obter os valores dos argumentos nomeados
bot.argumentos.nomeado_ou("nome") # "Alex"
bot.argumentos.nomeado_ou("nome", default="xpto") # "Alex"
bot.argumentos.nomeado_ou("idade") # "28 anos"

# Obter os valores dos argumentos nomeados que não foram informados
bot.argumentos.nomeado_ou("não_existente") # ""
bot.argumentos.nomeado_ou("não_existente", default="xpto") # "xpto"

# Obter os argumentos posicionais (Antes dos nomeados)
bot.argumentos.posicionais() # ["posicional", "outro posicional"]
