"""Módulo para navegadores Web
- Abstração do `Selenium`

```
# Navegadores
Edge, Chrome e Explorer
# Util
- Teclas: Teclas especiais para se enviar no método send_keys() de um WebElement
- ErroNavegador: Classe base para todas as exceções do `Selenium`
- ElementoNaoEncontrado: Exceção quando um elemento não é encontrado pelo método `encontrar_elemento`
```"""

from bot.navegador.setup import *