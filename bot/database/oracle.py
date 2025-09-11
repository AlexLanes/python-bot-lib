# std
import typing
# interno
import bot
from bot.database.setup import ResultadoSQL
# externo
import oracledb

class DatabaseOracle:
    """Classe para manipulação do Oracle Database
    - Abstração do `oracledb`

    ### Importante
    - Aberto transação automaticamente. Necessário realizar `commit()` para persistir alterações
    - Conexão fechada automaticamente ao sair do escopo ou manualmente com o `fechar_conexao()`
    - Utilizar o `OracleDatabase.configurar_cliente(caminho)` para problemas de **thick mode**
        - Necessário instalar o **Oracle instant client** e informar o `caminho` antes de abrir conexão

    ### Inicialização
    - Configurações para a conexão podem ser informadas no `**kwargs`, conforme aceito pelo `oracledb`
    - Exemplo: `user, password, host, port, service_name, instance_name`
    """

    conexao: oracledb.Connection
    """Objeto de conexão com o database"""

    @staticmethod
    def configurar_client (oracle_client: str) -> None:
        """Configurar o caminho para o diretório do **Oracle instant client**"""
        oracledb.init_oracle_client(lib_dir=oracle_client)

    def __init__ (self, **kwargs: typing.Any) -> None:
        """Criar conexão Oracle (autocommit sempre False)"""
        bot.logger.informar(f"Iniciando conexão Oracle Database")
        self.__criar_conexao = lambda: oracledb.connect(**kwargs)
        self.conexao = self.__criar_conexao()
        self.conexao.autocommit = False

    def __del__ (self) -> None:
        """Fechar a conexão quando sair do escopo"""
        try: self.fechar_conexao()
        except Exception: pass

    def __repr__ (self) -> str:
        return "<Database Oracle>"

    def fechar_conexao (self) -> None:
        """Fechar a conexão com o database
        - Executado automaticamente quando o objeto sair do escopo"""
        try:
            self.conexao.close()
            bot.logger.informar(f"Conexão com o {self!r} encerrada")
        except Exception: pass

    def reconectar (self) -> typing.Self:
        """Refazer a conexão caso encerrada"""
        try:
            with self.conexao.cursor() as c:
                c.execute("SELECT 1 FROM dual")
                c.fetchone()
            return self
        except oracledb.Error: pass

        try:
            if not self.conexao.is_healthy():
                self.conexao.close()
            del self.conexao
            self.conexao = self.__criar_conexao()
            self.conexao.autocommit = False
            return self
        except Exception as erro:
            raise Exception(f"Falha ao reconectar no {self!r}; {erro}") from None

    def tabelas (self, schema: str | None = None) -> list[tuple[str, str | None]]:
        """Nomes das tabelas e schemas disponíveis
        - `for tabela, schema in database.tabelas()`"""
        cursor = self.conexao.cursor()
        if schema: cursor.execute(
            "SELECT table_name, owner FROM all_tables WHERE owner = :schema",
            schema = schema.upper()
        )
        else: cursor.execute("SELECT table_name, owner FROM all_tables")

        itens = [(tabela, schema) for tabela, schema in cursor]
        itens.sort(key=lambda item: item[0]) # ordernar pelo nome das tabelas
        return itens

    def colunas (self, tabela: str, schema: str | None = None) -> list[tuple[str, str, str]]:
        """Informações das colunas da `tabela`
        - Retornado `[(coluna, tipo, nullable)]`"""
        cursor = self.conexao.cursor()
        if schema: cursor.execute(
            """
            SELECT column_name, data_type, nullable
            FROM all_tab_columns
            WHERE table_name = :tabela AND owner = :schema
            ORDER BY column_id
            """,
            tabela = tabela.upper(), schema = schema.upper()
        )
        else: cursor.execute(
            """
            SELECT column_name, data_type, nullable
            FROM user_tab_columns
            WHERE table_name = :tabela
            ORDER BY column_id
            """,
            tabela = tabela.upper()
        )
        return [tuple(item) for item in cursor]

    def commit (self) -> None:
        """Commitar alterações feitas na conexão"""
        self.conexao.commit()

    def rollback (self) -> None:
        """Reverter as alterações, pós commit, feitas na conexão"""
        self.conexao.rollback()

    def execute (self, sql: str, *posicional: bot.tipagem.tipoSQL, **nomeado: bot.tipagem.tipoSQL) -> ResultadoSQL:
        """Executar uma única instrução SQL
        - `sql` Comando que será executado
        - Recomendado ser parametrizado com argumentos posicionais `:1` **ou** nomeados `:nome`
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        assert bool(posicional) + bool(nomeado) < 2, "Não é possível misturar argumentos posicionais com nomeados"

        cursor = self.conexao.cursor()
        cursor.execute(sql, posicional if posicional else nomeado if nomeado else None)
        colunas = tuple(desc[0] for desc in cursor.description) if cursor.description else tuple()
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if not colunas and cursor.rowcount >= 0 else None,
            colunas = colunas,
            linhas = (tuple(linha) for linha in cursor) if colunas else (tuple() for _ in [])
        )

    def execute_many (self, sql: str, parametros: typing.Iterable[bot.tipagem.posicional] | typing.Iterable[bot.tipagem.nomeado]) -> ResultadoSQL:
        """Executar uma ou mais instruções SQL
        - `sql` Comando que será executado
        - `parametros` quantidade de argumentos, posicionais `:1` **ou** nomeados `:nome`, que serão executados
        - Retornado classe própria `ResultadoSQL`, veja a documentação na definição da classe"""
        cursor = self.conexao.cursor()
        cursor.executemany(sql, parametros)
        colunas = tuple(desc[0] for desc in cursor.description) if cursor.description else tuple()
        return ResultadoSQL(
            linhas_afetadas = cursor.rowcount if not colunas and cursor.rowcount >= 0 else None,
            colunas = colunas,
            linhas = (tuple(linha) for linha in cursor) if colunas else (tuple() for _ in [])
        )

__all__ = ["DatabaseOracle"]