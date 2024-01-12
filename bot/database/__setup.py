# std
import sqlite3
import re as regex
from typing import Iterable
# interno
import bot
# externo
import polars
import pyodbc


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
        # Verificar se o driver existe
        if not (drivers := [d for d in self.listar_drivers() if nomeDriver.lower() in d.lower()]): 
            raise ValueError(f"Driver ODBC '{ nomeDriver }' não encontrado")
        # Pegar um driver dos encontrados. Preferência ao UNICODE
        nomeDriver = unicode[0] if (unicode := [d for d in drivers if "unicode" in d.lower()]) \
                                else drivers[0]
        bot.logger.debug(f"Iniciando conexão com o database '{ nomeDriver }'")
        # Montar a conexão
        conexao = f"driver={ nomeDriver };"
        for configuracao in kwargs: conexao += f"{ configuracao }={ kwargs[configuracao] };"
        self.__conexao = pyodbc.connect(conexao, autocommit=False, timeout=5)

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        bot.logger.debug(f"Encerrando conexão com o database")
        if hasattr(self, "__conexao") and hasattr(self.__conexao, "close") and callable(self.__conexao.close): self.__conexao.close()
        else: del self

    def __repr__ (self) -> str:
        return f"<Database ODBC>"

    @property
    def tabelas (self) -> list[tuple[str, str | None]]:
        """Nomes das tabelas e schemas disponíveis
        - `for tabela, schema in database.tabelas()`"""
        cursor = self.__conexao.cursor()
        itens = [(tabela, schema if schema else None) for _, schema, tabela, *_ in cursor.tables(tableType="TABLE")]
        return sorted(itens, key=lambda item: item[0])

    def colunas (self, tabela: str, schema: str = None) -> list[tuple[str, str]]:
        """Nomes das colunas e tipos da tabela
        - `for coluna, tipo in database.colunas(tabela, schema)`"""
        cursor = self.__conexao.cursor()
        return [(item[3], item[5]) for item in cursor.columns(tabela, schema=schema)]

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

    @staticmethod
    def listar_drivers () -> list[str]:
        """Listar os ODBC drivers existentes no sistema
        - `@staticmethod`"""
        return pyodbc.drivers()


class Sqlite:
    """Classe de abstração do módulo `sqlite3`"""

    __conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database=":memory:") -> None:
        """Inicialização do banco de dados
        - `database` caminho para o arquivo .db ou .sqlite, 
        - Default carregar apenas na memória"""
        bot.logger.debug(f"Iniciando conexão com o database Sqlite")
        self.__conexao = sqlite3.connect(database, 5)
    
    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        bot.logger.debug(f"Encerrando conexão com o database")
        if hasattr(self, "__conexao") and hasattr(self.__conexao, "close") and callable(self.__conexao.close): self.__conexao.close()
        else: del self

    def __repr__ (self) -> str:
        return f"<Database Sqlite>"

    @property
    def tabelas (self) -> list[str]:
        """Nomes das tabelas disponíveis"""
        sql = "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        return [coluna for coluna, *_ in self.execute(sql)]

    def colunas (self, tabela: str) -> list[tuple[str, str]]:
        """Nomes das colunas e tipos da tabela
        - `for coluna, tipo in database.colunas(tabela, schema)`"""
        return [(coluna, tipo) 
                for _, coluna, tipo, *_, in self.execute(f"PRAGMA table_info({ tabela })")]

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

    def to_excel (self, caminho="resultado.xlsx") -> None:
        """Salvar as linhas de todas as tabelas da conexão em um arquivo excel"""
        for tabela in self.tabelas:
            self.execute(f"SELECT * FROM { tabela }") \
                .to_dataframe() \
                .write_excel(caminho, tabela, autofit=True)


__all__ = [
    "polars",
    "Sqlite",
    "DatabaseODBC"
]
