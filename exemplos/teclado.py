import bot

"""
Pressionar e soltar teclas
"""
bot.teclado.apertar("a", "A", "1", "ç").apertar("!", "🤣")
bot.teclado.apertar("page_down")
bot.teclado.apertar("home", "delete")

"""
Digitar os caracteres no texto
"""
bot.teclado.digitar(texto="")\
           .apertar("enter")

"""
Pressionar as teclas sequencialmente e soltá-las em ordem reversa
"""
bot.teclado.atalho("ctrl", "v")
bot.teclado.atalho("shift", "home")

"""
Pressionar as `teclas` e soltar ao sair
"""
with bot.teclado.pressionar("shift") as teclado:
    ...