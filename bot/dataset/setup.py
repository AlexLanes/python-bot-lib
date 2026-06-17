# std
from __future__ import annotations
# externo opcionais [dataset]
try: import polars, xlsxwriter, fastexcel
except ImportError: raise ImportError(
    "Dependência opcional 'bot[dataset]' necessária. "
    "Instale como 'bot[dataset]' para utilizar o módulo 'bot.dataset'"
)

def formatar_dataframe (df: "polars.DataFrame",
                        linhas_maximas = 1000,
                        esconder_shape = True,
                        tamanho_maximo_str = 1000,
                        esconder_tipo_coluna = True) -> str:
    """Formatar o `df` para sua versão em string"""
    kwargs = { 
        "tbl_rows": linhas_maximas, 
        "tbl_hide_dataframe_shape": esconder_shape, 
        "fmt_str_lengths": tamanho_maximo_str, 
        "tbl_hide_column_data_types": esconder_tipo_coluna 
    }
    with polars.Config(**kwargs):
        return str(df)

__all__ = ["formatar_dataframe"]