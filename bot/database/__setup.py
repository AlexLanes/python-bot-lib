# std
import re
from typing import Iterable
from sqlite3 import connect, Connection
# interno
import bot
# externo
import pandas
from xlsxwriter.worksheet import Worksheet


class Sqlite:
    """Classe de abstração do sqlite3"""

    conexao: Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database=":memory:") -> None:
        """Inicialização do banco de dados
        - `database` caminho para o arquivo .db ou .sqlite. `None` para carregar na memória"""
        bot.logger.debug(f"Iniciando conexão com o database '{ database }'")
        self.conexao = connect(database, 5)

    def __del__ (self):
        """Fechar a conexão quando sair do escopo"""
        bot.logger.debug(f"Encerrando conexão com o database")
        self.conexao.close()

    def commit (self) -> None:
        """Commitar alterações feitas na conexão"""
        self.conexao.commit()
    
    def rollback (self) -> None:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.conexao.rollback()
    
    @property
    def tabelas (self) -> dict[str, int]:
        """Mapa dos nomes das tabelas e quantidade de linhas"""
        obter_count = lambda tabela: [*self.execute(f"SELECT count(*) FROM { tabela }")][0][0]
        tabelas = self.execute("""SELECT name AS tabela FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'""")
        return { tabela: obter_count(tabela) for tabela, *_ in tabelas }

    def execute (self, sql: str, parametros: bot.tipagem.nomeado | bot.tipagem.posicional = None) -> bot.tipagem.ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Parâmetros presentes no `sql`"""
        cursor = self.conexao.execute(sql, parametros) if parametros else self.conexao.execute(sql)
        colunas = [coluna for coluna, *_ in cursor.description] if cursor.description else []
        gerador = ([valor for valor in linha] for linha in cursor)
        return bot.tipagem.ResultadoSQL(cursor.rowcount if cursor.rowcount >= 0 else None, colunas, gerador)

    def execute_many (self, sql: str, parametros: Iterable[bot.tipagem.nomeado] | Iterable[bot.tipagem.posicional]) -> bot.tipagem.ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado. Pode ser parametrizado com argumentos nomeados `:nome` ou posicionais `?`
        - `parametros` Lista dos parâmetros presentes no `sql`"""
        cursor = self.conexao.executemany(sql, parametros)
        colunas = [coluna for coluna, *_ in cursor.description] if cursor.description else []
        gerador = ([valor for valor in linha] for linha in cursor)
        return bot.tipagem.ResultadoSQL(cursor.rowcount if cursor.rowcount >= 0 else None, colunas, gerador)

    def to_excel (self, caminho="resultado.xlsx") -> None:
        """Salvar as linhas de todas as tabelas da conexão em um arquivo excel"""
        with pandas.ExcelWriter(caminho) as arquivo:
            for tabela in self.tabelas: self.execute(f"SELECT * FROM { tabela }")\
                                            .to_dataframe()\
                                            .to_excel(arquivo, tabela, index=False)
            ajustar_colunas_excel(arquivo)


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


__all__ = [
    "pandas",
    "Sqlite",
    "mapear_dtypes",
    "ajustar_colunas_excel"
]
