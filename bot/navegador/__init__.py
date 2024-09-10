"""Módulo para navegadores Web

# Navegadores
Edge, Chrome e Explorer

# Util
- Teclas: Teclas especiais para se enviar no método send_keys() de um WebElement
- ErroNavegador: Classe base para todas as exceções do `Selenium`
- ElementoNaoEncontrado: Exceção quando um elemento não é encontrado pelo método `encontrar_elemento`

# Variáveis .ini
- `[navegador] -> caminho_extensoes` 
    - `Opcional` caminhos para diretório de extensões, separados por vírgula, para utilizar no `Chrome` ou `Edge`
"""

from bot.navegador.setup import *