"""Pacote para ler e escrever dados estruturados como `xlsx` e `csv`
- Exportado `DataFrame` do pacote `polars`
## Dependência `bot[dataset]` necessária para utilizar `bot.dataset`"""

from bot.dataset.setup import *
from bot.dataset.excel import *
from bot.dataset.csv import *

try: from polars import DataFrame
except ImportError: pass