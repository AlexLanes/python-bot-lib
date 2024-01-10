# std
import sqlite3
import re as regex
from typing import Iterable
# interno
import bot
# externo
import pandas
import pyodbc
from xlsxwriter.worksheet import Worksheet


def mapear_dtypes (df: pandas.DataFrame) -> dict[str, str]:
    """Criar um dicionário { coluna: tipo } de um `pandas` dataframe"""
    linhas = [regex.split(r"\s+", linha)
              for linha in df.dtypes.to_string().split("\n")]
    return { coluna: tipo for coluna, tipo, *_ in linhas }


def ajustar_colunas_excel (excel: pandas.ExcelWriter) -> None:
    """Ajustar a largura das colunas de todas as planilhas no excel"""
    for nomePlanilha in excel.sheets:
        planilha: Worksheet = excel.sheets[nomePlanilha]
        planilha.autofit()


class DatabaseODBC:
    """Classe para manipulação de Databases via drivers ODBC
    - Necessário possuir o driver instalado em `ODBC Data Sources`
    - Abstração do `pyodbc`
    - Testado com PostgreSQL, MySQL e SQLServer"""

    __conexao: pyodbc.Connection
    """Objeto de conexão com o database"""

    def __init__ (self, nomeDriver: str, /, **kwargs) -> None:
        """Inicializar a conexão com o driver odbc
        - `odbc_driver` Não precisa ser exato mas deve estar em `Database.listar_drivers()`
        - Demais configurações para a conexão podem ser informadas no `**kwargs`
            - uid = usuário
            - pwd = senha
            - server = servidor
            - port = porta
            - database = nome do database"""
        if not (drivers := [d for d in self.listar_drivers() if nomeDriver.lower() in d.lower()]): 
            raise ValueError(f"Driver ODBC '{ nomeDriver }' não encontrado")

        nomeDriver = unicode[0] if (unicode := [d for d in drivers if "unicode" in d.lower()]) \
                                else drivers[0]
        bot.logger.debug(f"Iniciando conexão com o database '{ nomeDriver }'")

        conexao = f"driver={ nomeDriver };"
        for configuracao in kwargs: conexao += f"{ configuracao }={ kwargs[configuracao] };"
        self.__conexao = pyodbc.connect(conexao, autocommit=False, timeout=5)

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        bot.logger.debug(f"Encerrando conexão com o database")
        if hasattr(self, "__conexao") and hasattr(self.__conexao, "close") and callable(self.__conexao.close): self.__conexao.close()
        else: del self

    def __repr__(self) -> str:
        return f"<Database ODBC>"

    def commit (self) -> None:
        """Commitar alterações feitas na conexão"""
        self.__conexao.commit()

    def rollback (self) -> None:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.__conexao.rollback()
    
    def execute (self, sql: str, parametros: bot.tipagem.nomeado | bot.tipagem.posicional = None) -> bot.tipagem.ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Parâmetros presentes no `sql`"""
        # Transformar o sql e os parâmetros nomeados `:nome` para a forma posicional `?`
        # `pyodbc` não aceita parâmetros nomeados
        if isinstance(parametros, dict):
            parametros = { chave.lower(): valor for chave, valor in parametros.items() }
            parametros_existentes = [encontrado for encontrado in regex.findall(r":\w+", sql)
                                     if encontrado.lower()[1:] in parametros]
            parametros = [parametros[ existente.lower()[1:] ] for existente in parametros_existentes]
            # reversed para o replace não dar problema `(:id, :idade) -> (?, ?ade)`
            for existente in sorted(set(parametros_existentes), reverse=True): 
                sql = sql.replace(existente, "?")

        cursor = self.__conexao.execute(sql, parametros) if parametros else self.__conexao.execute(sql)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (tuple(linha) for linha in cursor)
        return bot.tipagem.ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: Iterable[bot.tipagem.nomeado] | Iterable[bot.tipagem.posicional]) -> bot.tipagem.ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - Utilizar apenas comandos SQL que resultem em `linhas_afetadas`
        - `sql` Comando que será executado. Deve ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Lista dos parâmetros presentes no `sql`
        - Parâmetros que apresentaram erro será feito log de alerta"""
        # executemany do `pyodbc` não retorna o rowcount
        total_linhas_afetadas = 0
        for parametro in parametros:
            try:
                resultado = self.execute(sql, parametro)
                if resultado.linhas_afetadas: total_linhas_afetadas += resultado.linhas_afetadas
            except pyodbc.DatabaseError as erro: 
                bot.logger.alertar(f"Erro ao executar o parâmetro { parametro }\n\t{ [*erro.args] }")
        return bot.tipagem.ResultadoSQL(total_linhas_afetadas, tuple(), (x for x in []))

    @property
    def tabelas_colunas (self) -> dict[str, list[str]]:
        """Mapa dos nomes das tabelas e colunas
        - tabela pode vir com o schema atribuído caso possua"""
        cursor = self.__conexao.cursor()
        schemas_tabelas = [(str(schema if schema else ""), str(tabela))
                           for _, schema, tabela, *_ in cursor.tables(tableType="TABLE")]
        return { f"{schema}.{tabela}" if schema else tabela: [item[3] for item in cursor.columns(tabela)]
                 for schema, tabela in schemas_tabelas }

    def to_excel (self, caminho="resultado.xlsx") -> None:
        """Salvar as linhas de todas as tabelas da conexão em um arquivo excel"""
        with pandas.ExcelWriter(caminho) as arquivo:
            for tabela in self.tabelas_colunas: self.execute(f"SELECT * FROM { tabela }")\
                                                    .to_dataframe()\
                                                    .to_excel(arquivo, tabela, index=False)
            ajustar_colunas_excel(arquivo)

    @staticmethod
    def listar_drivers () -> list[str]:
        """Listar os ODBC drivers existentes no sistema
        - `@staticmethod`"""
        return pyodbc.drivers()


class Sqlite (DatabaseODBC):
    """Classe de abstração do módulo `sqlite3`"""

    __conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database=":memory:") -> None:
        """Inicialização do banco de dados
        - `database` caminho para o arquivo .db ou .sqlite, 
        - Default carregar apenas na memória"""
        bot.logger.debug(f"Iniciando conexão com o database Sqlite")
        self.__conexao = sqlite3.connect(database, 5)

    def __repr__(self) -> str:
        return f"<Database Sqlite>"

    def execute (self, sql: str, parametros: bot.tipagem.nomeado | bot.tipagem.posicional = None) -> bot.tipagem.ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos posicionais `?` ou nomeados `:nome`
        - `parametros` Parâmetros presentes no `sql`"""
        cursor = self.__conexao.execute(sql, parametros) if parametros else self.__conexao.execute(sql)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return bot.tipagem.ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: Iterable[bot.tipagem.nomeado] | Iterable[bot.tipagem.posicional]) -> bot.tipagem.ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado. Deve ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Lista dos parâmetros presentes no `sql`"""
        cursor = self.__conexao.executemany(sql, parametros)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return bot.tipagem.ResultadoSQL(linhas_afetadas, colunas, gerador)

    @property
    def tabelas_colunas (self) -> dict[str, list[str]]:
        """Mapa dos nomes das tabelas e colunas"""
        obter_colunas = lambda tabela: [coluna for _, coluna, *_, in self.execute(f"PRAGMA table_info({ tabela })")]
        tabelas = self.execute("""SELECT name AS tabela FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'""")
        return { tabela: obter_colunas(tabela) for tabela, *_ in tabelas }


__all__ = [
    "pandas",
    "Sqlite",
    "DatabaseODBC",
    "mapear_dtypes",
    "ajustar_colunas_excel"
]
