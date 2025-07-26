import bot

"""
Enviar email para os destinatários com o assunto, conteúdo e anexos informados
Necessário utilizar as variáveis do configfile
    `[email.enviar] -> user, password, host, [port: 587, ssl: False, ]`
"""
# Simples
bot.email.enviar_email(
    destinatarios = ["alex.angelo@dclick.com.br", "outro@dclick.com.br"],
    assunto = "assunto do email",
    conteudo = "conteúdo do email"
)

# Com anexo
anexo_log = bot.estruturas.Caminho(".log")
anexo_documento = bot.estruturas.Caminho("documento.xlsx")
bot.email.enviar_email(
    destinatarios = ["alex.angelo@dclick.com.br", "outro@dclick.com.br"],
    assunto = "assunto do email",
    conteudo = "conteúdo do email",
    anexos = [anexo_log, anexo_documento]
)

# Com conteúdo HTML, caso começe com '<'
with open("arquivo.html", "r") as reader:
    conteudo_html = reader.read()
bot.email.enviar_email(
    destinatarios = ["alex.angelo@dclick.com.br", "outro@dclick.com.br"],
    assunto = "assunto do email",
    conteudo = conteudo_html
)



"""
Realizar a leitura de emails de uma caixa
Necessário utilizar as variáveis do configfile
    `[email.obter] -> user, password, host`
"""
emails = bot.email.obter_emails(
    # Quantidade limite de emails
        # `None` para não aplicar limite
        # `int` para obter os primeiros `n` emails
        # `slice` para obter um pedaço desejado
    limite = None,
    # search-criteria do IMAP para buscar apenas determinados emails
        # default são todos os emails = "ALL"
    query = "ALL",
    # Indicador para marcar o email como visualizado
    visualizar = False
)

# Retornado um `gernerator` para ser mais eficiente
# Dados incluídos em uma classe própria para armazenar os dados
for email in emails:
    email.uid           # id do email
    email.remetente     # quem enviou
    email.destinatarios # os que receberam
    email.assunto       # assunto do email
    email.data          # data de envio do email
    email.texto         # conteúdo do email como texto
    email.html          # conteúdo do email como html
    email.anexos        # lista com os anexos [(nome, tipo, conteúdo)]
