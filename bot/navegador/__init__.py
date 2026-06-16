"""Pacote para Navegadore Web utilizando o `selenium` como abstração

## Navegador
Classe base, herdada pelas implementações `Edge` `Chrome` `Explorer`, com métodos para manipulações e consultas.  
Navegadores são abertos em sua inicialização e fechados quando a sua referencia sair do escopo ou caso seja feito `del navegador`.  
Possível de se utilizar com o `with` para encerrar automaticamente

## Implementações
`Edge()`  
`Chrome()`  
`Explorer()`  
`Navegador.from_driver(driver, ...)` para criar o `Navegador` de um `ChromiumDriver` já inicializado  
`Navegador.from_chromium_binary("caminho", ...)` para criar o `Navegador` a partir do `caminho` executável para um `Chromium`  

## Util
- `Teclas` chars especiais para se enviar nos métodos `ElementoWEB.digitar()` ou `WebElement.send_keys()`
- `ErroNavegador` Classe base para todas as exceções do `Selenium`
- `ElementoNaoEncontrado` Exceção quando um elemento não é encontrado pelo método `Navegador.encontrar_elemento(localizador)`
"""

from bot.navegador.setup import *