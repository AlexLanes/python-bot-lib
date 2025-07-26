import bot

"""
Protocolo HTTP
"""
# Realizar requisições http conforme parâmetros
bot.http.request(...)
# Criar um cliente http pré configurado
cliente = bot.http.Client()
cliente.get(...)
cliente.post(...)
# Criar um cliente async http pré configurado
cliente = bot.http.AsyncClient()

# Classe para parse de um URL
url = bot.http.Url("https://docs.google.com/document/d/1BjpTaNbG4q5-M0yEYrCYJdxwtS0bUifW/edit?tab=t.0")
url.schema           # "https"
url.host             # "docs.google.com"
url.path             # "/document/d/1BjpTaNbG4q5-M0yEYrCYJdxwtS0bUifW/edit"
url.query.to_dict()  # {'tab': ['t.0']}
url.url              # Versão completa do URL

# Realizar o URL Encode em uma `str`
bot.http.Url.encode("") 
