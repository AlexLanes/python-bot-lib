"""Pacote para ler e escrever dados estruturados como `xlsx` e `csv`
- `DataFrame` exportado do `polars`
## Necessário `bot[dataset]` para instalar dependências do `bot.dataset`"""

from bot.dataset.setup import *
from bot.dataset.excel import *
from bot.dataset.csv import *

try: from polars import DataFrame
except ImportError: pass