# std
import sys, atexit, logging, typing, inspect, functools
from datetime import (
    datetime  as Datetime,
    timezone  as Timezone,
    timedelta as Timedelta
)
# interno
import bot
from bot.sistema import Caminho

class StackInfoFilter (logging.Filter):
    """Adicionar informação do arquivo, função e linha na mensagem do Log"""

    diretorio_execucao: str

    def __init__ (self, diretorio_execucao: Caminho, name: str = "") -> None:
        super().__init__(name)
        self.diretorio_execucao = diretorio_execucao.string

    def filter (self, record: logging.LogRecord) -> bool:
        try: frame = inspect.stack()[6]
        except Exception: return True

        caminho_relativo = frame.filename.removeprefix(self.diretorio_execucao).strip("\\")
        record.msg = f"arquivo({caminho_relativo}) | função({frame.function}) | linha({frame.lineno}) | {record.msg}"
        return True

class Logger:
    """Classe configurada para criar, consultar e tratar os arquivos de log.  
    Possível alterar configurações mudando as constantes antes do logger ser inicializado

    #### Inicializado automaticamente (Possível ser desativado)

    - Stream para o `stdout`
    - Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
    - Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
    - Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False, flag_desativar: False]`"""

    DESATIVAR: bool = False
    """Flag para não inicializar o logger"""
    INICIALIZADO: bool = False
    """Flag para checar se o logger já foi inicializado"""

    TIMEZONE_BR = Timezone(Timedelta(hours=-3))
    INICIALIZACAO_PACOTE = Datetime.now(TIMEZONE_BR)

    NOME_LOG = "BOT"
    FORMATO_DATA_LOG: str = r"%Y-%m-%dT%H:%M:%S"
    FORMATO_NOME_LOG_PERSISTENCIA: str = r"%Y-%m-%dT%H-%M-%S.log"
    FORMATO_MENSAGEM_LOG: str = "%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s"

    CAMINHO_LOG_RAIZ = Caminho.diretorio_execucao() / ".log"
    CAMINHO_DIRETORIO_PERSISTENCIA = Caminho.diretorio_execucao() / "logs"
    CAMINHO_LOG_PERSISTENCIA = Caminho(
        CAMINHO_DIRETORIO_PERSISTENCIA.string,
        INICIALIZACAO_PACOTE.strftime(FORMATO_NOME_LOG_PERSISTENCIA)
    )

    def __repr__ (self) -> str:
        return f"<bot.Logger nome='{self.logger.name}'>"

    @functools.cached_property
    def logger (self) -> logging.Logger:
        """Obter o `Logger` apropriado
        - `BOT` quando a flag `DESATIVAR=False` (Inicializa o logger)
        - `ROOT` quando a flag `DESATIVAR=True`"""
        self.DESATIVAR = self.DESATIVAR or bot.configfile.obter_opcao_ou("logger", "flag_desativar", False)
        if self.DESATIVAR:
            return logging.getLogger()

        logger = logging.getLogger(self.NOME_LOG)
        logger.propagate = False # Não deixar o root duplicar a mensagem
        try: return logger
        finally: self.inicializar_logger()

    def inicializar_logger (self) -> typing.Self:
        """Inicializar o logger
        - Configura o formato
        - Inicializa os handlers no stdout e arquivos
        - Registra a limpeza do diretório de persistência"""
        if self.INICIALIZADO: return self
        self.INICIALIZADO = True

        # Aplicar o filtro apenas para quem usar o BOT_LOGGER
        # Não possível usar em todos os handlers devido a diferença no stack de outros loggers
        if self.logger.name == self.NOME_LOG:
            diretorio_execucao = self.CAMINHO_LOG_RAIZ.parente
            self.logger.addFilter(StackInfoFilter(diretorio_execucao))

        # Adicionar os handlers
        self.CAMINHO_LOG_PERSISTENCIA.parente.criar_diretorios()
        for handler in (logging.FileHandler(self.CAMINHO_LOG_RAIZ.path, "w", "utf-8"),
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler(self.CAMINHO_LOG_PERSISTENCIA.path, "w", "utf-8")):
            self.logger.addHandler(handler)

        logging.basicConfig(
            force    = True,
            encoding = "utf-8",
            datefmt  = self.FORMATO_DATA_LOG,
            format   = self.FORMATO_MENSAGEM_LOG,
            level    = logging.DEBUG if bot.configfile.obter_opcao_ou("logger", "flag_debug", False) else logging.INFO,
            handlers = self.logger.handlers
        )

        atexit.register(self.__limpeza_diretorio_persistencia)
        return self

    def __limpeza_diretorio_persistencia (self) -> None:
        """Limpar os logs no `CAMINHO_DIRETORIO_PERSISTENCIA` que ultrapassaram a data limite
        - Registrado para executar ao fim do Python automaticamente
        - `Default:` 14 dias"""
        if not self.INICIALIZADO: return

        dias = bot.configfile.obter_opcao_ou("logger", "dias_persistencia", 14)
        limite = Timedelta(days=dias)

        for caminho in self.CAMINHO_DIRETORIO_PERSISTENCIA:
            if not caminho.arquivo(): continue
            data = Datetime.strptime(caminho.nome, self.FORMATO_NOME_LOG_PERSISTENCIA)\
                           .astimezone(self.TIMEZONE_BR)
            if self.INICIALIZACAO_PACOTE - data < limite: break
            caminho.apagar_arquivo()

    def debug (self, mensagem: str) -> typing.Self:
        """Log nível 'DEBUG'"""
        self.logger.debug(mensagem)
        return self

    def informar (self, mensagem: str) -> typing.Self:
        """Log nível 'INFO'"""
        self.logger.info(mensagem)
        return self

    def alertar (self, mensagem: str) -> typing.Self:
        """Log nível 'WARNING'"""
        self.logger.warning(mensagem)
        return self

    def erro (self, mensagem: str, excecao: Exception | None = None) -> typing.Self:
        """Log nível 'ERROR'
        - `excecao=None` Capturado automaticamente, caso esteja dentro do `except`"""
        self.logger.error(mensagem, exc_info=excecao or sys.exc_info())
        return self

    def linha_horizontal (self) -> typing.Self:
        """Adicionar uma linha horizontal para separar seções visualmente"""
        for handler in self.logger.handlers:
            if not isinstance(handler, (logging.FileHandler, logging.StreamHandler)): continue
            handler.stream.write("\n------------------- |\n\n")
            handler.flush()
        return self

    def limpar_log_raiz (self) -> typing.Self:
        """Limpar o `CAMINHO_LOG_RAIZ`
        - Não afeta o `CAMINHO_DIRETORIO_PERSISTENCIA`"""
        if not self.INICIALIZADO: return self

        self.logger.handlers[0].close()
        self.logger.handlers[0] = logging.FileHandler(self.CAMINHO_LOG_RAIZ.path, "w", "utf-8")
        self.logger.handlers[0].formatter = logging.Formatter(
            self.FORMATO_MENSAGEM_LOG,
            self.FORMATO_DATA_LOG
        )

        return self

logger = Logger()
"""Classe configurada para criar, consultar e tratar os arquivos de log.  
Possível alterar configurações mudando as constantes antes do logger ser inicializado

#### Inicializado automaticamente (Possível ser desativado)

- Stream para o `stdout`
- Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
- Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
- Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False, flag_desativar: False]`"""

__all__ = ["logger"]