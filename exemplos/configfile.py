import bot

"""
Classe para inicialização de variáveis a partir de arquivo de configuração `.ini`  

#### Inicializado automaticamente na primeira consulta

- Para concatenação de valores, utilizar a sintaxe `${opção}` `${seção:opção}`
- `$` é reservado, utilizar `$$` para contornar
- `#` ou `;` comenta a linha se tiver no começo
- Arquivos terminados em `.ini` devem estar presente em `DIRETORIO_EXECUCAO`

# Supondo que o arquivo .ini na raiz do projeto esteja da seguinte forma

[logger]
flag_debug = False
flag_persistencia = False
dias_persistencia = 14

[FTP]
host: test.rebex.net
user: demo 
password: password
timeout: 5
port: 21
"""

# Checar se existe uma seção do arquivo
bot.configfile.possui_secao("logger") # True
bot.configfile.possui_secao("não existente") # False

# Checar se uma ou mais opções existem em uma seção
bot.configfile.possui_opcao("logger", "flag_debug") # True
bot.configfile.possui_opcao("logger", "não existente") # False
bot.configfile.possui_opcoes("logger", "flag_debug", "flag_persistencia", "dias_persistencia") # True

# Obter as seções do arquivo
bot.configfile.obter_secoes() # ["logger", "ftp"]

# Obter as opções de uma seção
bot.configfile.opcoes_secao("logger") # ["flag_debug", "flag_persistencia", "dias_persistencia"]

# Obter o valor de uma seção/opção ou default caso não exista
bot.configfile.obter_opcao_ou("logger", "dias_persistencia") # "14"
bot.configfile.obter_opcao_ou("logger", "dias_persistencia", default=0) # 14
bot.configfile.obter_opcao_ou("logger", "não existente", default=0) # 0

# Obter múltiplas opções de uma seção e erro caso alguma não exista
bot.configfile.obter_opcoes_obrigatorias("ftp", "host", "user", "password") # ("test.rebex.net", "demo", "password")
