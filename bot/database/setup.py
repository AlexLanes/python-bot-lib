# std
import re, typing
import itertools, functools, dataclasses
# interno
from .. import tipagem, database, logger, sistema
# externo
import polars, pyodbc
from xlsxwriter import Workbook

cache = {}
def sql_nomeado_para_posicional (sql: str, parametros: tipagem.nomeado) -> tuple[str, list[str]]:
    """Transformar o sql parametrizado `nomeado` para `posicional`
    - `index[0]` SQL transformado
    - `index[1]` Ordem dos nomes parametrizados no `sql`"""
    if sql in cache: return cache[sql]

    sql_transformado = sql
    ordem_nomes = [
        nome
        for nome in re.findall(r"(?<=:)\w+", sql)
        if nome in parametros
    ]

    # converter SQL
    ordenar_por_tamanho = { "key": lambda x: len(x), "reverse": True }
    for nome in sorted(ordem_nomes, **ordenar_por_tamanho): 
        sql_transformado = sql_transformado.replace(f":{nome}", "?", 1)

    # inserir no `cache` e retornar
    resultado = (sql_transformado, ordem_nomes)
    cache[sql] = resultado
    return resultado

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
    with database.polars.Config(**kwargs):
        return str(df)

def criar_excel (caminho: sistema.Caminho, planilhas: dict[str, polars.DataFrame]) -> sistema.Caminho:
    """Criar um arquivo excel em `caminho` com os dados informados em `planilhas`
    - `planilhas` Dicionário sendo a `key` o nome da planilha e `value` um `polars.Dataframe` com os dados
    - `caminho` deve terminar em `.xlsx`"""
    assert caminho.nome.endswith(".xlsx"), "Caminho deve terminar em '.xlsx'"

    with Workbook(caminho.string) as excel:
        for nome_planilha, df in planilhas.items():
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
    linhas: typing.Iterable[tuple[tipagem.tipoSQL, ...]]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    @functools.cached_property
    def quantidade_linhas (self) -> int:
        """Obter a quantidade de linhas retornadas sem consumir o gerador"""
        self.linhas, linhas = itertools.tee(self.linhas)
        return sum(1 for _ in linhas)

    @functools.cached_property
    def primeira_linha (self) -> tuple[tipagem.tipoSQL, ...] | None:
        """Cache da primeira linha no resultado
        - Não altera o gerador das `linhas`
        - `None` caso não possua"""
        self.linhas, linhas = itertools.tee(self.linhas)
        try: return next(linhas)
        except StopIteration: return None

    def __iter__ (self) -> typing.Generator[tuple[tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    def __repr__ (self) -> str:
        "Representação da classe"
        if self.linhas_afetadas is not None:
            return f"<ResultadoSQL com {self.linhas_afetadas} linha(s) afetada(s)"
        if linhas := len(self):
            return f"<ResultadoSQL com '{len(self.colunas)}' coluna(s) e '{linhas}' linha(s)"
        return f"<ResultadoSQL vazio>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return "vazio" not in repr(self)

    def __len__ (self) -> int:
        return self.quantidade_linhas

    def __getitem__ (self, campo: str) -> tipagem.tipoSQL:
        """Obter o `campo` da primeira linha"""
        if not self.primeira_linha: return
        return self.primeira_linha[self.colunas.index(campo)]

    def to_dict (self) -> list[dict[str, tipagem.tipoSQL]]:
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

class DatabaseODBC:
    """Classe para manipulação de Databases via drivers ODBC
    - Necessário possuir o driver instalado em `ODBC Data Sources`
    - Abstração do `pyodbc`
    - Testado com PostgreSQL, MySQL e SQLServer"""

    odbc_args: str
    """Argumentos de conexão ODBC"""
    conexao: pyodbc.Connection
    """Objeto de conexão com o database"""

    def __init__ (self, nome_driver: str, **kwargs: str) -> None:
        """Inicializar a conexão com o driver odbc
        - `odbc_driver` Não precisa ser exato mas deve estar em `DatabaseODBC.listar_drivers()`
        - Demais configurações para a conexão podem ser informadas no `**kwargs`
            - uid = usuário
            - pwd = senha
            - server = servidor
            - port = porta
            - database = nome do database  
        - `BoolsAsChar=0` para o PostgreSQL retornar os `BOOLEAN` como `bool` e não `str`"""
        # verificar se o driver existe
        existentes = [driver for driver in self.listar_drivers() 
                      if nome_driver.lower() in driver.lower()]
        if not existentes: raise ValueError(f"Driver ODBC '{nome_driver}' não encontrado")

        # escolher um driver dos encontrados (preferência ao `unicode`)
        unicode = [driver for driver in existentes if "unicode" in driver.lower()]
        nome_driver = unicode[0] if unicode else existentes[0]
        logger.informar(f"Iniciando conexão ODBC com o driver '{nome_driver}'")

        # montar a conexão
        kwargs["driver"] = nome_driver
        self.odbc_args = ";".join(
            f"{nome}={valor}" 
            for nome, valor in kwargs.items()
        )
        self.conexao = pyodbc.connect(self.odbc_args, autocommit=False, timeout=5)

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        try: self.fechar_conexao()
        except Exception: pass

    def __repr__ (self) -> str:
        return f"<Database ODBC>"

    def fechar_conexao (self) -> None:
        """Fechar a conexão com o database
        - Executado automaticamente quando o objeto sair do escopo"""
        self.conexao.close()
        logger.informar(f"Conexão com o database encerrada")

    def tabelas (self, schema: str | None = None) -> list[tuple[str, str | None]]:
        """Nomes das tabelas e schemas disponíveis
        - `for tabela, schema in database.tabelas()`"""
        cursor = self.conexao.cursor()
        itens = [
            (tabela, schema if schema else None)
            for _, schema, tabela, *_ in cursor.tables(tableType="TABLE", schema=schema)
        ]
        itens.sort(key=lambda item: item[0]) # ordernar pelo nome das tabelas
        return itens

    def colunas (self, tabela: str, schema: str | None = None) -> list[tuple[str, str]]:
        """Nomes das colunas e tipos da tabela
        - `for coluna, tipo in database.colunas(tabela, schema)`"""
        cursor = self.conexao.cursor()
        return [
            (item[3], item[5])
            for item in cursor.columns(tabela, schema=schema)
        ]

    def commit (self) -> None:
        """Commitar alterações feitas na conexão"""
        self.conexao.commit()

    def rollback (self) -> None:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.conexao.rollback()

    def reconectar (self) -> None:
        """Refaz a conexão caso encerrada"""
        try: self.conexao.execute("SELECT 1")
        except pyodbc.OperationalError:
            self.conexao = pyodbc.connect(self.odbc_args, autocommit=False, timeout=5)

    def execute (self, sql: str, parametros: tipagem.nomeado | tipagem.posicional | None = None) -> ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Parâmetros presentes no `sql`"""
        # `pyodbc` não aceita parâmetros nomeados
        if isinstance(parametros, dict):
            ref_parametros = parametros
            sql, nomes = sql_nomeado_para_posicional(sql, parametros) # type: ignore
            parametros = [ref_parametros[nome] for nome in nomes]

        cursor = self.conexao.execute(sql, parametros) if parametros else self.conexao.execute(sql)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (tuple(linha) for linha in cursor)
        return ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: typing.Iterable[tipagem.nomeado] | typing.Iterable[tipagem.posicional]) -> ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - Utilizar apenas comandos SQL que resultem em `linhas_afetadas`
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` `Iterable` dos parâmetros presentes no `sql`
        - Parâmetros que apresentaram erro será feito log de alerta"""
        # executemany do `pyodbc` não retorna o rowcount
        total_linhas_afetadas = 0
        for parametro in parametros:
            try:
                resultado = self.execute(sql, parametro)
                if resultado.linhas_afetadas: total_linhas_afetadas += resultado.linhas_afetadas
            except pyodbc.DatabaseError as erro: 
                logger.alertar(f"Erro ao executar o parâmetro {parametro}\n\t{[ *erro.args ]}")
        return ResultadoSQL(total_linhas_afetadas, tuple(), (x for x in []))

    @staticmethod
    def listar_drivers () -> list[str]:
        """Listar os ODBC drivers existentes no sistema
        - `@staticmethod`"""
        return pyodbc.drivers()

__all__ = [
    "polars",
    "criar_excel",
    "DatabaseODBC",
    "formatar_dataframe"
]