# externo
import polars
from polars import DataFrame

def formatar_dataframe (df: DataFrame,
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

__all__ = [
    "polars",
    "DataFrame",
    "formatar_dataframe"
]