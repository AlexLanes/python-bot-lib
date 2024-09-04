# std
import re, sqlite3, typing
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

class DatabaseODBC:
    """Classe para manipulação de Databases via drivers ODBC
    - Necessário possuir o driver instalado em `ODBC Data Sources`
    - Abstração do `pyodbc`
    - Testado com PostgreSQL, MySQL e SQLServer"""

    __conexao: pyodbc.Connection
    """Objeto de conexão com o database"""

    def __init__ (self, nome_driver: str, /, **kwargs: dict[str, str]) -> None:
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
        conexao = ";".join(f"{nome}={valor}" 
                           for nome, valor in kwargs.items())
        self.__conexao = pyodbc.connect(conexao, autocommit=False, timeout=5)

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        logger.informar(f"Encerrando conexão com o database")
        try: self.__conexao.close()
        except: pass

    def __repr__ (self) -> str:
        return f"<Database ODBC>"

    def tabelas (self, schema: str = None) -> list[tuple[str, str | None]]:
        """Nomes das tabelas e schemas disponíveis
        - `for tabela, schema in database.tabelas()`"""
        cursor = self.__conexao.cursor()
        itens = [
            (tabela, schema if schema else None)
            for _, schema, tabela, *_ in cursor.tables(tableType="TABLE", schema=schema)
        ]
        itens.sort(key=lambda item: item[0]) # ordernar pelo nome das tabelas
        return itens

    def colunas (self, tabela: str, schema: str = None) -> list[tuple[str, str]]:
        """Nomes das colunas e tipos da tabela
        - `for coluna, tipo in database.colunas(tabela, schema)`"""
        cursor = self.__conexao.cursor()
        return [
            (item[3], item[5])
            for item in cursor.columns(tabela, schema=schema)
        ]

    def commit (self) -> None:
        """Commitar alterações feitas na conexão"""
        self.__conexao.commit()

    def rollback (self) -> None:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.__conexao.rollback()

    def execute (self, sql: str, parametros: tipagem.nomeado | tipagem.posicional = None) -> estruturas.ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Parâmetros presentes no `sql`"""
        # `pyodbc` não aceita parâmetros nomeados
        if isinstance(parametros, dict):
            ref_parametros = parametros
            sql, nomes = sql_nomeado_para_posicional(sql, parametros)
            parametros = [ref_parametros[nome] for nome in nomes]

        cursor = self.__conexao.execute(sql, parametros) if parametros else self.__conexao.execute(sql)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (tuple(linha) for linha in cursor)
        return estruturas.ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: typing.Iterable[tipagem.nomeado] | typing.Iterable[tipagem.posicional]) -> estruturas.ResultadoSQL:
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
        return estruturas.ResultadoSQL(total_linhas_afetadas, tuple(), (x for x in []))

    @staticmethod
    def listar_drivers () -> list[str]:
        """Listar os ODBC drivers existentes no sistema
        - `@staticmethod`"""
        return pyodbc.drivers()

class Sqlite:
    """Classe de abstração do módulo `sqlite3`"""

    __conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database: str | estruturas.Caminho = ":memory:") -> None:
        """Inicialização do banco de dados
        - `database` caminho para o arquivo .db ou .sqlite, 
        - Default carregar apenas na memória"""
        database = str(database)
        logger.informar(f"Iniciando conexão Sqlite com o database '{database}'")
        self.__conexao = sqlite3.connect(database, autocommit=False)
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
        return [tabela for tabela, *_ in self.execute(sql)]

    def colunas (self, tabela: str) -> list[tuple[str, str]]:
        """Nomes das colunas e tipos da tabela
        - `for coluna, tipo in database.colunas(tabela)`"""
        return [
            (coluna, tipo)
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

    def execute (self, sql: str, parametros: tipagem.nomeado | tipagem.posicional = None) -> estruturas.ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Parâmetros presentes no `sql`"""
        cursor = self.__conexao.execute(sql, parametros) if parametros else self.__conexao.execute(sql)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return estruturas.ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: typing.Iterable[tipagem.nomeado] | typing.Iterable[tipagem.posicional]) -> estruturas.ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado. Recomendado ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Lista dos parâmetros presentes no `sql`"""
        cursor = self.__conexao.executemany(sql, parametros)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return estruturas.ResultadoSQL(linhas_afetadas, colunas, gerador)

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
