"""Módulo para navegadores Web

# Navegadores
Edge, Chrome e Explorer

# Util
- Teclas: Teclas especiais para se enviar no método send_keys() de um WebElement
- ErroNavegador: Classe base para todas as exceções do `Selenium`
- ElementoNaoEncontrado: Exceção quando um elemento não é encontrado pelo método `encontrar_elemento`

# Variáveis .ini
- `[navegador] -> caminho_perfil` 
    - `Opcional` informar um caminho de perfil para o `Chrome` ou `Edge` (Carrega as extensões do perfil)
    - `Default` criado um perfil vazio e apagado após fechar
    - `chrome://version/` para ver o perfil de execução de um usuário
"""

from bot.navegador.setup import *