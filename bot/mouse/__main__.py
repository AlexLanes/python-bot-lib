import bot

print(
    "",
    "# ------------------------------------------------------------- #",
    "# Executando módulo 'bot.mouse'                                 #",
    "# Será feito o print() da posição e cor RGB a cada 0.2 segundos #",
    "# CTRL + C no terminal para encerrar o loop                     #",
    "# ------------------------------------------------------------- #",
    "",
    sep = "\n"
)

while bot.mouse.sleep(0.2):
    print(
        "Posição Atual ", bot.mouse.posicao_atual(),
        " | Cor ", bot.mouse.rgb(),
        sep = "",
    )