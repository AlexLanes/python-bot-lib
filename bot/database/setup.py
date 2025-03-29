# std
import re, sqlite3, typing
import itertools, functools, dataclasses
# interno
from .. import tipagem, database, logger, estruturas
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

def criar_excel (caminho: estruturas.Caminho, planilhas: dict[str, polars.DataFrame]) -> estruturas.Caminho:
    """Criar um arquivo excel com os dados informados
    - `planilhas` Dicionário sendo a `key` o nome da planilha e `value` um `polars.Dataframe` com os dados
    - `caminho` deve terminar em `.xlsx`"""
    assert caminho.nome.endswith(".xlsx"), "Caminho deve terminar em '.xlsx'"

    with Workbook(caminho.string) as excel:
        for nome_planilha, df in planilhas.items():
            df.write_excel(excel, nome_planilha, autofit=True)

    return caminho

@dataclasses.dataclass
class ResultadoSQL:
    """Classe utilizada no retorno de comando em banco de dados

    ```
    # representação "vazio", "com linhas afetadas" ou "com colunas e linhas"
    repr(resultado)
    resultado.linhas_afetadas != None # para comandos de manipulação
    resultado.colunas # para comandos de consulta

    # teste de sucesso, indica se teve linhas_afetadas ou linhas/colunas retornadas
    bool(resultado) | if resultado: ...

    # quantidade de linhas retornadas
    len(resultado)

    # iteração sobre as linhas `Generator`
    # as linhas são consumidas quando iteradas sobre
    linha: tuple[tipagem.tipoSQL, ...] = next(resultado.linhas)
    for linha in resultado.linhas:
    for linha in resultado:

    # fácil acesso a primeira linha
    resultado["nome_coluna"]
    ```"""

    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica para o comando sql"""
    colunas: tuple[str, ...]
    """Colunas das linhas retornadas (se houver)"""
    linhas: typing.Iterable[tuple[tipagem.tipoSQL, ...]]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    def __iter__ (self) -> typing.Generator[tuple[tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    @functools.cached_property
    def __p (self) -> tuple[tipagem.tipoSQL, ...] | None:
        """Cache da primeira linha no resultado
        - `None` caso não possua"""
        self.linhas, linhas = itertools.tee(self.linhas)
        try: return next(linhas)
        except StopIteration: return None

    def __repr__ (self) -> str:
        "Representação da classe"
        tipo = f"com {self.linhas_afetadas} linha(s) afetada(s)" if self.linhas_afetadas \
            else f"com {len(self.colunas)} coluna(s) e {len(self)} linha(s)" if self.__p \
            else f"vazio"
        return f"<ResultadoSQL {tipo}>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return "vazio" not in repr(self)

    def __len__ (self) -> int:
        """Obter a quantidade de linhas no retornadas"""
        self.linhas, linhas = itertools.tee(self.linhas)
        return sum(1 for _ in linhas)

    def __getitem__ (self, campo: str) -> tipagem.tipoSQL:
        """Obter o `campo` da primeira linha"""
        return self.__p[self.colunas.index(campo)] if self.__p else None

    def to_dict (self) -> dict[str, int | None | list[dict]]:
        """Representação formato dicionário"""
        self.linhas, linhas = itertools.tee(self.linhas)
        return {
            "linhas_afetadas": self.linhas_afetadas,
            "resultados": [
                { 
                    coluna: valor
                    for coluna, valor in zip(self.colunas, linha)
                }
                for linha in linhas
            ]
        }

    def to_dataframe (self, transformar_string=False) -> polars.DataFrame:
        """Salvar o resultado em um `polars.DataFrame`
        - `transformar_string` flag se os dados serão convertidos em `str`"""
        self.linhas, linhas = itertools.tee(self.linhas)
        to_string = lambda linha: tuple(
            str(valor) if valor != None else None
            for valor in linha
        )
        return polars.DataFrame(
            map(to_string, linhas) if transformar_string else linhas,
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
        - `odbc_driver` Não precisa ser exato mas deve estar em `Database.listar_drivers()`
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
        logger.informar(f"Encerrando conexão com o database")
        try: self.conexao.close()
        except: pass

    def __repr__ (self) -> str:
        return f"<Database ODBC>"

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

class Sqlite:
    """Classe de abstração do módulo `sqlite3`
    - `database` caminho para o arquivo .db ou .sqlite (Default apenas na memória)
    - Comando para ativar as `foreign_keys` realizado automaticamente
    - Aberto transação automaticamente. Necessário realizar `commit()` para persistir alterações"""

    __conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database: str | estruturas.Caminho = ":memory:") -> None:
        database = str(database)
        logger.informar(f"Iniciando conexão Sqlite com o database '{database}'")
        self.__conexao = sqlite3.connect(database)
        self.__conexao.execute("PRAGMA foreign_keys = ON")

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        logger.informar(f"Encerrando conexão com o database")
        try: self.__conexao.close()
        except: pass

    def __repr__ (self) -> str:
        return f"<Database Sqlite>"

    def tabelas (self) -> list[str]:
        """Nomes das tabelas disponíveis"""
        sql = "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        return [str(tabela) for tabela, *_ in self.execute(sql)]

    def colunas (self, tabela: str) -> list[tuple[str, str]]:
        """Nomes das colunas e tipos da tabela
        - `for coluna, tipo in database.colunas(tabela)`"""
        return [
            (str(coluna), str(tipo))
            for _, coluna, tipo, *_, in self.execute(f"PRAGMA table_info({tabela})")
        ]

    def commit (self) -> typing.Self:
        """Commitar alterações feitas na conexão"""
        self.__conexao.commit()
        return self

    def rollback (self) -> typing.Self:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.__conexao.rollback()
        return self

    def execute (self, sql: str, parametros: tipagem.nomeado | tipagem.posicional | None = None) -> ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Parâmetros presentes no `sql`"""
        cursor = self.__conexao.execute(sql, parametros) if parametros else self.__conexao.execute(sql) # type: ignore
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: typing.Iterable[tipagem.nomeado] | typing.Iterable[tipagem.posicional]) -> ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Lista dos parâmetros presentes no `sql`"""
        cursor = self.__conexao.executemany(sql, parametros) # type: ignore
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return ResultadoSQL(linhas_afetadas, colunas, gerador)

    def to_excel (self, caminho: estruturas.Caminho) -> estruturas.Caminho:
        """Salvar as linhas de todas as tabelas da conexão no `caminho` formato excel
        - `caminho` deve terminar com `.xlsx`"""
        return criar_excel(caminho, {
            tabela: self.execute(f"SELECT * FROM {tabela}").to_dataframe()
            for tabela in self.tabelas()
        })

__all__ = [
    "polars",
    "Sqlite",
    "criar_excel",
    "DatabaseODBC",
    "formatar_dataframe"
]