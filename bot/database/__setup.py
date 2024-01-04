# std
import re
import sqlite3
from typing import Iterable
from collections import defaultdict
# interno
import bot
# externo
import pandas
import pyodbc
from xlsxwriter.worksheet import Worksheet


def mapear_dtypes (df: pandas.DataFrame) -> dict:
    """Criar um dicionário { coluna: tipo } de um `pandas` dataframe"""
    mapa = {}
    for colunaTipo in df.dtypes.to_string().split("\n"):
        coluna, tipo, *_ = re.split(r"\s+", colunaTipo)
        mapa[coluna] = tipo
    return mapa


def ajustar_colunas_excel (excel: pandas.ExcelWriter) -> None:
    """Ajustar a largura das colunas de todas as planilhas no excel"""
    for nomePlanilha in excel.sheets:
        planilha: Worksheet = excel.sheets[nomePlanilha]
        planilha.autofit()


class Database:
    """Classe para manipulação de Database ODBC
    - Necessário possuir o driver instalado em `ODBC Data Sources`
    - Abstração do `pyodbc`"""

    conexao: pyodbc.Connection
    """Objeto de conexão com o database"""

    def __init__ (self, odbc_driver: str, servidor: str, database: str, usuario: str = None, senha: str = None, /, **kwargs) -> None:
        """Inicializar a conexão com o driver odbc
        - Demais configurações de conexão podem ser especificadas no `kwargs`"""
        bot.logger.debug(f"Iniciando conexão com o database '{ odbc_driver }'")

        conexao = f"driver={ odbc_driver };server={ servidor };database={ database };"
        if usuario: conexao += f"uid={ usuario };"
        if senha: conexao += f"pwd={ senha };"
        for chave in kwargs: conexao += f"{ chave }={ kwargs[chave] };"

        self.conexao = pyodbc.connect(conexao, autocommit=False, timeout=5)

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        bot.logger.debug(f"Encerrando conexão com o database")
        if hasattr(self, "conexao") and hasattr(self.conexao, "close") and callable(self.conexao.close): self.conexao.close()
        else: del self

    def __repr__(self) -> str:
        return f"<Database ODBC>"

    def commit (self) -> None:
        """Commitar alterações feitas na conexão"""
        self.conexao.commit()

    def rollback (self) -> None:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.conexao.rollback()

    def execute (self, sql: str, parametros: bot.tipagem.nomeado | bot.tipagem.posicional = None) -> bot.tipagem.ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Parâmetros presentes no `sql`"""
        cursor = self.conexao.execute(sql, parametros) if parametros else self.conexao.execute(sql)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return bot.tipagem.ResultadoSQL(linhas_afetadas, colunas, gerador)

    def execute_many (self, sql: str, parametros: Iterable[bot.tipagem.nomeado] | Iterable[bot.tipagem.posicional]) -> bot.tipagem.ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - utilizar apenas para saber a quantidade de `linhas_afetadas`
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Lista dos parâmetros presentes no `sql`"""
        # executemany do `pyodbc` não retorna o rowcount
        linhas_afetadas = 0
        for parametro in parametros:
            cursor = self.conexao.execute(sql, parametro)
            if cursor.rowcount > 0: linhas_afetadas += cursor.rowcount
        return bot.tipagem.ResultadoSQL(linhas_afetadas, tuple(), (x for x in []))

    @property
    def tabelas (self) -> dict[str, list[str]]:
        """Mapa dos nomes das tabelas e colunas"""
        mapa = defaultdict(list)
        for _, schema, tabela, coluna, *_ in self.conexao.cursor().columns():
            chave = f"{ schema }.{ tabela }" if schema else tabela
            mapa[chave].append(coluna)
        return mapa

    def to_excel (self, caminho="resultado.xlsx") -> None:
        """Salvar as linhas de todas as tabelas da conexão em um arquivo excel"""
        with pandas.ExcelWriter(caminho) as arquivo:
            for tabela in self.tabelas: self.execute(f"SELECT * FROM { tabela }")\
                                            .to_dataframe()\
                                            .to_excel(arquivo, tabela, index=False)
            ajustar_colunas_excel(arquivo)


class Sqlite (Database):
    """Classe de abstração do módulo `sqlite3`"""

    conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database=":memory:") -> None:
        """Inicialização do banco de dados
        - `database` caminho para o arquivo .db ou .sqlite. `None` para carregar na memória"""
        bot.logger.debug(f"Iniciando conexão com o database Sqlite")
        self.conexao = sqlite3.connect(database, 5)
    
    def execute_many (self, sql: str, parametros: Iterable[bot.tipagem.nomeado] | Iterable[bot.tipagem.posicional]) -> bot.tipagem.ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Lista dos parâmetros presentes no `sql`"""
        cursor = self.conexao.executemany(sql, parametros)
        colunas = tuple(coluna[0] for coluna in cursor.description) if cursor.description else tuple()
        linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 and not colunas else None
        gerador = (linha for linha in cursor)
        return bot.tipagem.ResultadoSQL(linhas_afetadas, colunas, gerador)
    
    @property
    def tabelas (self) -> dict[str, list[str]]:
        """Mapa dos nomes das tabelas e colunas"""
        obter_colunas = lambda tabela: [coluna for _, coluna, *_, in self.execute(f"PRAGMA table_info({ tabela })")]
        tabelas = self.execute("""SELECT name AS tabela FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'""")
        return { tabela: obter_colunas(tabela) for tabela, *_ in tabelas }


__all__ = [
    "pandas",
    "Sqlite",
    "Database",
    "mapear_dtypes",
    "ajustar_colunas_excel"
]
