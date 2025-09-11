# std
import sqlite3, typing
# interno
import bot
from bot.database.setup import criar_excel, ResultadoSQL

class Sqlite:
    """Classe de abstração do módulo `sqlite3`
    - `database` caminho para o arquivo .db ou .sqlite (Default apenas na memória)
    - Aberto transação automaticamente. Necessário realizar `commit()` para persistir alterações
    - Conexão fechada automaticamente ao sair do escopo ou manualmente com o `fechar_conexao()`"""

    conexao: sqlite3.Connection
    """Conexão com o sqlite3"""

    def __init__ (self, database: str | bot.sistema.Caminho = ":memory:", **kwargs: typing.Any) -> None:
        database = str(database)
        bot.logger.informar(f"Iniciando conexão Sqlite com o database '{database}'")
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
        bot.logger.informar(f"Conexão com o {self!r} encerrada")

    def tabelas (self) -> list[str]:
        """Nomes das tabelas disponíveis"""
        sql = "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        return [str(tabela) for tabela, *_ in self.execute(sql)]

    def colunas (self, tabela: str) -> list[tuple[str, str, bool]]:
        """Informações das colunas da `tabela`
        - Retornado `[(coluna, tipo, nullable)]`"""
        return [
            (str(coluna), str(tipo), not bool(notnull))
            for _, coluna, tipo, notnull, *_ in self.execute(f"PRAGMA table_info({tabela})")
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

    def execute (self, sql: str, *posicional: bot.tipagem.tipoSQL, **nomeado: bot.tipagem.tipoSQL) -> ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado
        - Recomendado ser parametrizado com argumentos posicionais `?` **ou** nomeados `:nome`
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        assert bool(posicional) + bool(nomeado) < 2, "Não é possível misturar argumentos posicionais com nomeados"
        cursor = self.conexao.execute(sql, posicional or nomeado)
        colunas = tuple(coluna for coluna, *_ in cursor.description) if cursor.description else tuple()
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if not colunas and cursor.rowcount >= 0 else None,
            colunas = colunas,
            linhas = (linha for linha in cursor) if colunas else (tuple() for _ in [])
        )

    def execute_many (self, sql: str, parametros: typing.Iterable[bot.tipagem.posicional] | typing.Iterable[bot.tipagem.nomeado]) -> ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado
        - `parametros` quantidade de argumentos, posicionais `?` **ou** nomeados `:nome`, que serão executados
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        cursor = self.conexao.executemany(sql, parametros) # type: ignore
        colunas = tuple(coluna for coluna, *_ in cursor.description) if cursor.description else tuple()
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if not colunas and cursor.rowcount >= 0 else None,
            colunas = colunas,
            linhas = (linha for linha in cursor) if colunas else (tuple() for _ in [])
        )

    def to_excel (self, caminho: bot.sistema.Caminho) -> bot.sistema.Caminho:
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