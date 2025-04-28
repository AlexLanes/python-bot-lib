"""Pacote para tratar argumentos de inicialização do Python
- Argumentos posicionais devem vir antes dos nomeados
- Argumentos nomeados: `--nome valor`
- Cobrir argumentos com aspas, caso possua espaço

Exemplo: `python main.py posicional_1 "posicional 2" --nome "Alex Lanes"`"""

from bot.argumentos.setup import *