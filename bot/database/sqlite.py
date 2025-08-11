# std
import sqlite3, typing
# interno
from .setup import criar_excel, ResultadoSQL
from .. import logger, sistema, tipagem

class Sqlite:
    """Classe de abstração do módulo `sqlite3`
    - `database` caminho para o arquivo .db ou .sqlite (Default apenas na memória)
    - Aberto transação automaticamente. Necessário realizar `commit()` para persistir alterações
    - Conexão fechada automaticamente ao sair do escopo ou manualmente com o `fechar_conexao()`"""

    conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database: str | sistema.Caminho = ":memory:", **kwargs: typing.Any) -> None:
        database = str(database)
        logger.informar(f"Iniciando conexão Sqlite com o database '{database}'")
        self.conexao = sqlite3.connect(database, **kwargs)

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        try: self.fechar_conexao()
        except Exception: pass

    def __repr__ (self) -> str:
        return f"<Database Sqlite>"

    def fechar_conexao (self) -> None:
        """Fechar a conexão com o `sqlite`
        - Executado automaticamente quando o objeto sair do escopo"""
        self.conexao.close()
        logger.informar(f"Conexão com o sqlite encerrada")

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
        self.conexao.commit()
        return self

    def rollback (self) -> typing.Self:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.conexao.rollback()
        return self

    def ativar_foreign_keys (self) -> typing.Self:
        """Realizar o comando para ativar as `foreign_keys`"""
        self.conexao.execute("PRAGMA foreign_keys = ON")
        return self

    def execute (self, sql: str, *posicional: tipagem.tipoSQL, **nomeado: tipagem.tipoSQL) -> ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado
        - Recomendado ser parametrizado com argumentos posicionais `?` **ou** nomeados `:nome`
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        assert bool(posicional) + bool(nomeado) < 2, "Não é possível misturar argumentos posicionais com nomeados"
        cursor = self.conexao.execute(sql, posicional or nomeado)
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 else None,
            colunas = tuple(coluna for coluna, *_ in cursor.description) if cursor.description else tuple(),
            linhas = (linha for linha in cursor)
        )

    def execute_many (self, sql: str, parametros: typing.Iterable[tipagem.nomeado] | typing.Iterable[tipagem.posicional]) -> ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado
        - `parametros` quantidade de argumentos, posicionais `?` **ou** nomeados `:nome`, que serão executados
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        cursor = self.conexao.executemany(sql, parametros) # type: ignore
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if cursor.rowcount >= 0 else None,
            colunas = tuple(coluna for coluna, *_ in cursor.description) if cursor.description else tuple(),
            linhas = (linha for linha in cursor)
        )

    def to_excel (self, caminho: sistema.Caminho) -> sistema.Caminho:
        """Salvar as linhas de todas as tabelas da conexão no `caminho` formato excel
        - `caminho` deve terminar com `.xlsx`"""
        return criar_excel(
            caminho,
            {
                tabela: self.execute(f"SELECT * FROM {tabela}").to_dataframe()
                for tabela in self.tabelas()
            }
        )

__all__ = ["Sqlite"]