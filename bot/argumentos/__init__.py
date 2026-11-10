"""Pacote para obter argumentos de inicialização do Python
- Argumentos posicionais devem vir antes dos nomeados
- Argumentos nomeados: `--nome valor`
- Cobrir argumentos com aspas, caso possua espaço

### Exemplo
> `python main.py arg1 "arg 2" --nome Alex --idade 29`
```python
#-- Argumentos Posicionais --#
posicionais = bot.argumentos.posicionais()
assert posicionais == ["arg1", "arg 2"]

#-- Checando existência de Argumentos Nomeados --#
assert bot.argumentos.nomeado_existe("nome")  == True
assert bot.argumentos.nomeado_existe("idade") == True
assert bot.argumentos.nomeado_existe("xpto")  == False

#-- Obter valor de Argumentos Nomeados --#
assert bot.argumentos.nomeado_ou("nome") == "Alex"
assert bot.argumentos.nomeado_ou("idade", default=0) == 29
assert bot.argumentos.nomeado_ou("xpto", default="") == ""
```"""

from bot.argumentos.setup import *