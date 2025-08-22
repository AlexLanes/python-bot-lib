# std
import typing
import itertools, functools, dataclasses
# interno
import bot
# externo
import polars
from xlsxwriter import Workbook

def formatar_dataframe (df: polars.DataFrame,
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
    with bot.database.polars.Config(**kwargs):
        return str(df)

@bot.estruturas.Resultado.decorador
def escapar_tag_xml (df: polars.DataFrame) -> polars.DataFrame:
    return df.select([
        polars.col(col)
            .str.replace_all("<", "&lt;")
            .str.replace_all(">", "&gt;")
        if df.schema[col] == polars.String
        else polars.col(col)

        for col in df.columns
    ])

def criar_excel (caminho: bot.sistema.Caminho, planilhas: dict[str, polars.DataFrame]) -> bot.sistema.Caminho:
    """Criar um arquivo excel em `caminho` com os dados informados em `planilhas`
    - `planilhas` Dicionário sendo a `key` o nome da planilha e `value` um `polars.Dataframe` com os dados
    - `caminho` deve terminar em `.xlsx`"""
    assert caminho.nome.endswith(".xlsx"), "Caminho deve terminar em '.xlsx'"

    with Workbook(caminho.string) as excel:
        for nome_planilha, df in planilhas.items():
            df = escapar_tag_xml(df).valor_ou(df)
            df.write_excel(excel, nome_planilha, autofit=True)

    return caminho

@dataclasses.dataclass
class ResultadoSQL:
    """Classe utilizada no retorno ao executar comando em banco de dados

    ### Representação
    ```
    - repr(resultado) # vazio, com linhas afetadas ou com colunas e linhas
    - resultado.linhas_afetadas != None # para comandos de manipulação
    - resultado.colunas e resultado.linhas # para comandos de consulta
    ```

    ### Indicador se teve linhas_afetadas ou linhas retornadas
    ```
    - bool(resultado)
    - if resultado: ...
    ```

    ### Quantidade de linhas retornadas
    ```
    - len(resultado)
    - resultado.quantidade_linhas
    ```

    ### Iteração sobre as linhas retornadas
    ```
    # As linhas são consumidas quando iteradas sobre
    - linha: tuple[tipagem.tipoSQL, ...] = next(resultado.linhas)
    - for linha in resultado.linhas: ...
    - for linha in resultado: ...
    - resultado.to_dict()
    - resultado.to_dataframe()
    ```

    ### Fácil acesso a primeira linha
    ```
    - resultado["nome_coluna"]
    - resultado.primeira_linha["nome_coluna"]
    ```
    """

    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica ao comando sql"""
    colunas: tuple[str, ...]
    """Colunas das linhas retornadas (se houver)"""
    linhas: typing.Iterable[tuple[bot.tipagem.tipoSQL, ...]]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    @functools.cached_property
    def quantidade_linhas (self) -> int:
        """Obter a quantidade de linhas retornadas sem consumir o gerador"""
        self.linhas, linhas = itertools.tee(self.linhas)
        return sum(1 for _ in linhas)

    @functools.cached_property
    def primeira_linha (self) -> tuple[bot.tipagem.tipoSQL, ...] | None:
        """Cache da primeira linha no resultado
        - Não altera o gerador das `linhas`
        - `None` caso não possua"""
        self.linhas, linhas = itertools.tee(self.linhas)
        try: return next(linhas)
        except StopIteration: return None

    def __iter__ (self) -> typing.Generator[tuple[bot.tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    def __repr__ (self) -> str:
        "Representação da classe"
        if (self.linhas_afetadas or 0) >= 1:
            return f"<ResultadoSQL com {self.linhas_afetadas} linha(s) afetada(s)"
        if self.quantidade_linhas:
            return f"<ResultadoSQL com '{len(self.colunas)}' coluna(s) e '{self.quantidade_linhas}' linha(s)"
        return f"<ResultadoSQL vazio>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return "vazio" not in repr(self)

    def __len__ (self) -> int:
        return self.quantidade_linhas

    def __getitem__ (self, campo: str) -> bot.tipagem.tipoSQL:
        """Obter o `campo` da primeira linha"""
        if not self.primeira_linha: return
        return self.primeira_linha[self.colunas.index(campo)]

    def to_dict (self) -> list[dict[str, bot.tipagem.tipoSQL]]:
        """Representação das linhas e colunas no formato `dict`
        - Consome o gerador das `linhas`"""
        return [
            { 
                coluna: valor
                for coluna, valor in zip(self.colunas, linha)
            }
            for linha in self
        ]

    def to_dataframe (self, transformar_string=False) -> polars.DataFrame:
        """Salvar o resultado em um `polars.DataFrame`
        - `transformar_string` flag se os dados serão convertidos em `str`
        - Consome o gerador das `linhas`"""
        to_string = lambda linha: tuple(
            str(valor) if valor != None else None
            for valor in linha
        )
        return polars.DataFrame(
            map(to_string, self.linhas) if transformar_string else self.linhas,
            { coluna: str for coluna in self.colunas } if transformar_string else self.colunas,
            nan_to_null=True
        )

__all__ = [
    "polars",
    "criar_excel",
    "formatar_dataframe"
]