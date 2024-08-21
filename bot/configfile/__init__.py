"""Módulo para inicialização de variáveis a partir de arquivo de configuração
- Para concatenação de valores, utilizar a sintaxe `${opção} ou ${seção:opção}`
- `$` é reservado, utilizar `$$` para contornar
- `#` é reservado para comentar a linha, colocar o valor entre aspas
- Arquivo terminado em `.ini` deve estar presente na raiz do projeto
    - Caso o `bot.configurar_diretorio()` não tenha sido utilizado, o diretório de execução será utilizado

Exemplo:
```
[logger]
flag_debug = False
flag_persistencia = False
dias_persistencia = 14

[FTP]
host = test.rebex.net
user = demo 
password = password
timeout = 5
port = 21
```"""

from .__setup import *