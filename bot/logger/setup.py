# std
import sys, atexit, logging, typing, inspect, functools
from datetime import (
    datetime  as Datetime,
    timezone  as Timezone,
    timedelta as Timedelta
)
# interno
from ..        import configfile
from ..sistema import Caminho

DIRETORIO_EXECUCAO = Caminho.diretorio_execucao().string

class StackInfoFilter (logging.Filter):
    """Adicionar informação do arquivo, função e linha na mensagem do Log"""

    def filter (self, record: logging.LogRecord) -> bool:
        try: frame = inspect.stack()[6]
        except Exception: return True

        caminho_relativo = frame.filename.removeprefix(DIRETORIO_EXECUCAO).strip("\\")
        record.msg = f"arquivo({caminho_relativo}) | função({frame.function}) | linha({frame.lineno}) | {record.msg}"
        return True

class Logger:
    """Classe configurada para criar, consultar e tratar os arquivos de log.  
    Possível alterar configurações mudando as constantes antes do logger ser inicializado

    #### Deve ser inicializado `bot.logger.inicializar_logger()`

    - Stream para o `stdout`
    - Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
    - Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
    - Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False]`"""

    INICIALIZADO = False
    TIMEZONE_BR = Timezone(Timedelta(hours=-3))
    INICIALIZACAO_PACOTE = Datetime.now(TIMEZONE_BR)

    FORMATO_DATA_LOG = r"%Y-%m-%dT%H:%M:%S"
    FORMATO_NOME_LOG_PERSISTENCIA = r"%Y-%m-%dT%H-%M-%S.log"
    FORMATO_MENSAGEM_LOG = "%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s"

    CAMINHO_LOG_RAIZ = Caminho.diretorio_execucao() / ".log"
    CAMINHO_DIRETORIO_PERSISTENCIA = Caminho.diretorio_execucao() / "logs"
    CAMINHO_LOG_PERSISTENCIA = Caminho(
        CAMINHO_DIRETORIO_PERSISTENCIA.string,
        INICIALIZACAO_PACOTE.strftime(FORMATO_NOME_LOG_PERSISTENCIA)
    )

    @functools.cached_property
    def root_logger (self) -> logging.Logger:
        return logging.getLogger()

    @functools.cached_property
    def bot_logger (self) -> logging.Logger:
        logger = logging.getLogger("BOT")
        logger.propagate = False # Não deixar o root duplicar a mensagem
        return logger

    def inicializar_logger (self) -> typing.Self:
        """Inicializar o logger
        - Configura o formato
        - Inicializa os handlers no stdout e arquivos
        - Registra a limpeza do diretório de persistência"""
        if self.INICIALIZADO: return self
        self.INICIALIZADO = True

        # Aplicar o filtro apenas para quem usar o BOT_LOGGER
        # Não possível usar em todos os handlers devido a diferença no stack de outros loggers
        self.bot_logger.addFilter(StackInfoFilter())

        # Adicionar os handlers no BOT_LOGGER
        self.CAMINHO_LOG_PERSISTENCIA.parente.criar_diretorios()
        for handler in (logging.FileHandler(self.CAMINHO_LOG_RAIZ.path, "w", "utf-8"),
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler(self.CAMINHO_LOG_PERSISTENCIA.path, "w", "utf-8")):
            self.bot_logger.addHandler(handler)

        logging.basicConfig(
            force    = True,
            encoding = "utf-8",
            datefmt  = self.FORMATO_DATA_LOG,
            format   = self.FORMATO_MENSAGEM_LOG,
            level    = logging.DEBUG if configfile.obter_opcao_ou("logger", "flag_debug", False) else logging.INFO,
            handlers = self.bot_logger.handlers
        )

        atexit.register(self.__limpeza_diretorio_persistencia)
        return self

    def __limpeza_diretorio_persistencia (self) -> None:
        """Limpar os logs no `CAMINHO_DIRETORIO_PERSISTENCIA` que ultrapassaram a data limite
        - Registrado para executar ao fim do Python automaticamente
        - `Default:` 14 dias"""
        # obter limite
        dias = configfile.obter_opcao_ou("logger", "dias_persistencia", 14)
        limite = Timedelta(days=dias)
        # limpar
        for caminho in Logger.CAMINHO_DIRETORIO_PERSISTENCIA:
            if not caminho.arquivo(): continue
            data = Datetime.strptime(caminho.nome, Logger.FORMATO_NOME_LOG_PERSISTENCIA)\
                           .astimezone(Logger.TIMEZONE_BR)
            if Logger.INICIALIZACAO_PACOTE - data < limite: break
            caminho.apagar_arquivo()

    def debug (self, mensagem: str) -> typing.Self:
        """Log nível 'DEBUG'"""
        logger = self.bot_logger if self.INICIALIZADO else self.root_logger
        logger.debug(mensagem)
        return self

    def informar (self, mensagem: str) -> typing.Self:
        """Log nível 'INFO'"""
        logger = self.bot_logger if self.INICIALIZADO else self.root_logger
        logger.info(mensagem)
        return self

    def alertar (self, mensagem: str) -> typing.Self:
        """Log nível 'WARNING'"""
        logger = self.bot_logger if self.INICIALIZADO else self.root_logger
        logger.warning(mensagem)
        return self

    def erro (self, mensagem: str, excecao: Exception | None = None) -> typing.Self:
        """Log nível 'ERROR'
        - `excecao=None` Capturado automaticamente, caso esteja dentro do `except`"""
        logger = self.bot_logger if self.INICIALIZADO else self.root_logger
        logger.error(mensagem, exc_info=excecao or sys.exc_info())
        return self

    def linha_horizontal (self) -> typing.Self:
        """Adicionar uma linha horizontal para separar seções visualmente"""
        for handler in self.bot_logger.handlers:
            if not isinstance(handler, (logging.FileHandler, logging.StreamHandler)): continue
            handler.stream.write("\n------------------- |\n\n")
            handler.flush()
        return self

    def limpar_log_raiz (self) -> typing.Self:
        """Limpar o `CAMINHO_LOG_RAIZ`
        - Não afeta o `CAMINHO_DIRETORIO_PERSISTENCIA`"""
        self.bot_logger.handlers[0].close()
        self.bot_logger.handlers[0] = logging.FileHandler(self.CAMINHO_LOG_RAIZ.path, "w", "utf-8")
        return self

logger = Logger()
"""Classe configurada para criar, consultar e tratar os arquivos de log.  
Possível alterar configurações mudando as constantes antes do logger ser inicializado

#### Deve ser inicializado `bot.logger.inicializar_logger()`

- Stream para o `stdout`
- Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
- Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
- Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False]`"""

__all__ = ["logger"]