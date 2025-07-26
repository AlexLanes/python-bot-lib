import bot

"""
Protocolo FTP
Variáveis configfile
    `[FTP] -> host, [user, password, timeout: 5.0, port: 21]`
"""
ftp = bot.ftp.FTP()                             # Iniciando conexão
ftp.diretorio                                   # Diretório atual da conexão
ftp.alterar_diretorio("/outro/diretorio")       # Alterar o diretório da conexão
ftp.listar_diretorio()                          # Listar os `arquivos, diretórios` do diretório atual
ftp.obter_arquivo("arquivo.txt")                # Obter conteúdo do arquivo no diretório atual
ftp.renomear_arquivo("arquivo.txt", "abc.txt")  # Renomear arquivo no diretório atual
ftp.remover_arquivo("arquivo.txt")              # Remover arquivo no diretório atual

# Adicionar o arquivo no diretório atual
with open("arquivo.txt") as reader:
    ftp.adicionar_arquivo("arquivo.txt", reader)
