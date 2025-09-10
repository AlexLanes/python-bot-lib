# std
import typing
# interno
import bot
from bot.database.setup import ResultadoSQL
# externo
import pyodbc

class DatabaseODBC:
    """Classe para manipulação de Databases via driver ODBC
    - Abstração do `pyodbc`
    - Testado com PostgreSQL, MySQL e SQLServer

    ### Importante
    - Necessário possuir o driver do banco de dados instalado em `ODBC Data Sources`
    - Aberto transação automaticamente. Necessário realizar `commit()` para persistir alterações
    - Conexão fechada automaticamente ao sair do escopo ou manualmente com o `fechar_conexao()`

    ### Inicialização
    - `nome_driver` Nome do odbc driver. Não precisa ser exato mas deve estar em `DatabaseODBC.listar_drivers()`
    - `timeout` tempo limite para obter a conexão
    - `encoding` utilizado na conversão de strings para o Python. `None` usado o default do `pyodbc`
    - Demais configurações para a conexão podem ser informadas no `**kwargs`
        - `uid` usuário
        - `pwd` senha
        - `server` servidor
        - `port` porta
        - `database` nome do database  
        - `BoolsAsChar=0` para o PostgreSQL retornar os `BOOLEAN` como `bool` e não `str`
    """

    conexao: pyodbc.Connection
    """Objeto de conexão com o database"""

    def __init__ (self, nome_driver: str, timeout: int = 5, encoding: str | None = None, **kwargs: str | int) -> None:
        # verificar se o driver existe
        existentes = [driver for driver in self.listar_drivers() 
                      if nome_driver.lower() in driver.lower()]
        if not existentes: raise ValueError(f"Driver ODBC '{nome_driver}' não encontrado")
        # escolher um driver dos encontrados (preferência ao `unicode`)
        unicode = [driver for driver in existentes if "unicode" in driver.lower()]
        nome_driver = unicode[0] if unicode else existentes[0]
        bot.logger.informar(f"Iniciando conexão ODBC com o driver '{nome_driver}'")

        # montar o argumento de conexão
        kwargs["driver"] = nome_driver
        odbc_args = ";".join(
            f"{nome}={valor}" 
            for nome, valor in kwargs.items()
        )

        # criar conexão
        kwargs_pydobc = {
            "autocommit": False,
            "timeout": timeout
        }
        if encoding: kwargs["encoding"] = encoding
        self.__criar_conexao = lambda: pyodbc.connect(odbc_args, **kwargs_pydobc)
        self.conexao = self.__criar_conexao()

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
        bot.logger.informar(f"Conexão com o {self!r} encerrada")

    def reconectar (self) -> typing.Self:
        """Refazer a conexão caso encerrada"""
        try:
            self.conexao.execute("SELECT 1")
            return self
        except pyodbc.OperationalError: pass

        try:
            if not self.conexao.closed:
                self.conexao.close()
            del self.conexao
            self.conexao = self.__criar_conexao()
            return self
        except Exception as erro:
            raise Exception(f"Falha ao reconectar no {self!r}; {erro}") from None

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

    def execute (self, sql: str, *posicional: bot.tipagem.tipoSQL) -> ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado
        - Recomendado ser parametrizado com argumentos posicionais `?`
        - Argumentos nomeados `:nome` não são aceitos pelo `pyodbc`
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        cursor = self.conexao.execute(sql, posicional)
        colunas = tuple(coluna for coluna, *_ in cursor.description) if cursor.description else tuple()
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if not colunas and cursor.rowcount >= 0 else None,
            colunas = colunas,
            linhas = (tuple(linha) for linha in cursor) if colunas else (tuple() for _ in [])
        )

    def execute_many (self, sql: str, parametros: typing.Iterable[bot.tipagem.posicional], fast=False) -> None:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado
        - `parametros` quantidade de argumentos posicionais `?` que serão executados
        - `fast` Parâmetro especial do `pyodbc` para acelerar o `execute_many`, utilizar com cautela
        - O `pyodbc` não retorna a quantidade de linhas afetadas no `execute_many`
            - Utilizar o `execute` em loop caso seja necessário"""
        cursor = self.conexao.cursor()
        cursor.fast_executemany = fast
        cursor.executemany(sql, parametros) # type: ignore
        cursor.close()

    @staticmethod
    def listar_drivers () -> list[str]:
        """Listar os ODBC drivers existentes no sistema
        - `@staticmethod`"""
        return pyodbc.drivers()

__all__ = ["DatabaseODBC"]