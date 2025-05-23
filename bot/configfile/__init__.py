"""Pacote para inicialização de variáveis a partir de arquivo de configuração `.ini`
- Para concatenação de valores, utilizar a sintaxe `${opção} ou ${seção:opção}`
- `$` é reservado, utilizar `$$` para contornar
- `#` comenta a linha apenas se tiver no começo
- Arquivo terminado em `.ini` deve estar presente na raiz do projeto
    - Caso o `bot.configurar_diretorio()` não tenha sido utilizado, o diretório de execução será utilizado

Exemplo:
```
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
```"""

from bot.configfile.setup import *