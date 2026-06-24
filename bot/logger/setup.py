# std
import sys, uuid, atexit, typing, logging, functools
from datetime import datetime as Datetime, timedelta as Timedelta
# interno
import bot
from bot.sistema import Caminho
from bot.tempo import TIMEZONE_BRT
from bot.tipagem import SupportsStr

P = typing.ParamSpec("P")

class JsonFormatter (logging.Formatter):
    """Formato JSON Lines"""

    def __init__ (self, identificador: str, diretorio_execucao: str, *, adicionar_file=True) -> None:
        super().__init__()
        self.identificador = identificador
        self.diretorio_execucao = diretorio_execucao
        self.adicionar_file = adicionar_file

    @typing.override
    def format (self, record: logging.LogRecord) -> str:
        payload: dict[str, SupportsStr] = {
            "id": self.identificador,
            "timestamp": Datetime.fromtimestamp(record.created, TIMEZONE_BRT)\
                                 .strftime(MainLogger.FORMATO_DATA_LOG),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if trace := getattr(record, "trace", None):
            payload["trace"] = trace
        if extra := getattr(record, "extra", None):
            payload["extra"] = extra

        # Informações sobre Exception
        try:
            if record.exc_info and isinstance(record.exc_info[1], Exception):
                payload["exception"] = {
                    "type": type(record.exc_info[1]).__name__,
                    "message": str(record.exc_info[1]),
                    "traceback": self.formatException(record.exc_info),
                }
        except Exception: pass

        # Informações sobre Arquivo
        if self.adicionar_file:
            payload["file"] = {
                "path": (record.pathname.removeprefix(self.diretorio_execucao)
                                        .lstrip("\\")
                                        .replace("\\", "/")),
                "function": record.funcName,
                "line": record.lineno,
            }

        return (
            bot.formatos.Json(payload)
            .stringify(indentar=False)
        )

class StdoutFilter (logging.Filter):
    """Permitir apenas logs `INFO` para os `MainLogger` e `WARNING` para loggers terceiros"""

    @typing.override
    def filter (self, record: logging.LogRecord) -> bool:
        if record.name in MainLogger.NOMES_MAIN_LOGGERS:
            return record.levelno >= logging.INFO
        return record.levelno >= logging.WARNING

class FileFilter (logging.Filter):
    """Permitir apenas todos os logs para os `MainLogger` e `INFO` para loggers terceiros"""

    @typing.override
    def filter (self, record: logging.LogRecord) -> bool:
        if record.name in MainLogger.NOMES_MAIN_LOGGERS:
            return True
        return record.levelno >= logging.INFO

class TracerLogger:
    """Classe logger, obtida pelo `MainLogger`, para realizar o rastreamento de itens relacionados
    - Utilizar o `tracer.encerrar()` para sinalizar a finalização do rastreamento"""

    def __init__ (self, logger: logging.Logger,
                        extra: dict[str, object]) -> None:
        self.extra = extra
        self.logger = logger
        self.encerrado = False
        self.id = uuid.uuid4().hex[:8]
        self.cronometro = bot.tempo.Cronometro()

    def __repr__ (self) -> str:
        return f"<bot.TracerLogger id='{self.id}' nome='{self.logger.name}'>"

    def __enter__ (self) -> typing.Self:
        return self

    def __exit__ (self, exc_type, exc: Exception | None, tb) -> None:
        if self.encerrado:
            return
        self.encerrado = True

        if exc is None: self.logger.info(
            "Tracer encerrado automaticamente com sucesso",
            stacklevel = 2,
            extra = {
                "extra": self.extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": "SUCCESS",
                    "seconds": self.cronometro()
                }
            }
        )

        else: self.logger.error(
            "Tracer encerrado automaticamente com erro",
            stacklevel = 2,
            exc_info = exc,
            extra = {
                "extra": self.extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": "ERROR",
                    "seconds": self.cronometro()
                }
            }
        )

    def __del__ (self) -> None:
        """Garantir encerramento ao sair do escopo"""
        if self.encerrado: return
        self.logger.warning(
            "Tracer não encerrado corretamente",
            exc_info = sys.exc_info(),
            extra = self.extra | {
                "trace": {
                    "id": self.id,
                    "status": "WARNING",
                    "seconds": self.cronometro()
                }
            }
        )

    def debug (self, mensagem: SupportsStr,
                     **extra: object) -> typing.Self:
        """Log nível `DEBUG`"""
        self.logger.debug(
            str(mensagem),
            stacklevel = 2,
            extra = {
                "extra": extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": "PROCESSING",
                    "seconds": self.cronometro()
                }
            }
        )
        return self

    def informar (self, mensagem: SupportsStr,
                        **extra: object) -> typing.Self:
        """Log nível `INFO`"""
        self.logger.info(
            str(mensagem),
            stacklevel = 2,
            extra = {
                "extra": extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": "PROCESSING",
                    "seconds": self.cronometro()
                }
            }
        )
        return self

    def alertar (self, mensagem: SupportsStr,
                       **extra: object) -> typing.Self:
        """Log nível `WARNING`
        - `Exception` capturada automaticamente, caso dentro do `except`"""
        self.logger.warning(
            str(mensagem),
            stacklevel = 2,
            exc_info = erro if any(erro := sys.exc_info()) else None,
            extra = {
                "extra": extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": "PROCESSING",
                    "seconds": self.cronometro()
                }
            }
        )
        return self

    def erro (self, mensagem: SupportsStr,
                    excecao: Exception | None = None,
                    **extra: object) -> typing.Self:
        """Log nível `ERROR`
        - `excecao=None` capturada automaticamente, caso esteja dentro do `except`"""
        self.logger.error(
            str(mensagem),
            stacklevel = 2,
            exc_info = excecao or sys.exc_info(),
            extra = {
                "extra": extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": "PROCESSING",
                    "seconds": self.cronometro()
                }
            }
        )
        return self

    def encerrar (self, status: typing.Literal["SUCCESS", "WARNING", "ERROR"],
                        mensagem: SupportsStr,
                        excecao: Exception | None = None,
                        **extra: object) -> None:
        """Sinalizar o encerramento do tracer
        - `excecao=None` capturada automaticamente, caso esteja dentro do `except`"""
        if self.encerrado: return
        self.encerrado = True

        log_func = {
            "SUCCESS": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
        }.get(status)
        assert log_func is not None, f"Status '{status}' inválido ao encerrar {self}"

        log_func(
            str(mensagem),
            stacklevel = 2,
            exc_info = excecao or (erro if any(erro := sys.exc_info()) else None),
            extra = {
                "extra": extra | self.extra,
                "trace": {
                    "id": self.id,
                    "status": status,
                    "seconds": self.cronometro()
                }
            }
        )

class MainLogger:
    """Classe pré-configurada para criar, consultar e tratar os arquivos de log
    - `name` o mesmo da propriedade que aparecerá nos logs

    #### Inicializar manualmente `logger.inicializar_logger()`
        - Stream para o `stdout`
        - Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
        - Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
        - Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False]`"""

    NOMES_MAIN_LOGGERS = set[str]()
    IDENTIFICADOR_LOGGER = uuid.uuid4().hex[:8]
    INICIALIZACAO_PACOTE = Datetime.now(TIMEZONE_BRT)

    FORMATO_DATA_LOG: str = r"%Y-%m-%dT%H:%M:%S"
    FORMATO_NOME_LOG_PERSISTENCIA: str = r"%Y-%m-%dT%H-%M-%S.jsonl"

    CAMINHO_LOG_RAIZ = Caminho.diretorio_execucao() / "log.jsonl"
    CAMINHO_DIRETORIO_PERSISTENCIA = Caminho.diretorio_execucao() / "logs"
    CAMINHO_LOG_PERSISTENCIA = Caminho(
        CAMINHO_DIRETORIO_PERSISTENCIA.string,
        INICIALIZACAO_PACOTE.strftime(FORMATO_NOME_LOG_PERSISTENCIA)
    )

    def __init__ (self, nome: str) -> None:
        self.__nome = nome
        MainLogger.NOMES_MAIN_LOGGERS.add(nome)

    def __repr__ (self) -> str:
        return f"<bot.MainLogger nome='{self.__nome}'>"

    @classmethod
    def obter_logger (cls, nome: str) -> "MainLogger":
        """Obter uma nova instância do `MainLogger` de `name="nome"`"""
        return cls(nome)

    @functools.cached_property
    def logger (self) -> logging.Logger:
        """Instância nomeada do `Logger`"""
        return logging.getLogger(self.__nome)

    def inicializar_logger (self) -> typing.Self:
        """Inicializar o logger pelo `ROOT` para capturar todas as mensagens
        - Formatação JSONL
        - Handlers no `stdout` e `arquivos`
        - Registra a limpeza do diretório de persistência"""
        atexit.register(self.__limpeza_diretorio_persistencia)
        self.CAMINHO_LOG_PERSISTENCIA.parente.criar_diretorios()

        # Root Handler
        root = self.logger.root
        root.setLevel(logging.DEBUG
                      if bot.configfile.obter_opcao_ou("logger", "flag_debug", False)
                      else logging.INFO)
        for handler in root.handlers:
            root.removeHandler(handler.close() or handler)

        # Adicionar File Handlers
        for handler in (logging.FileHandler(self.CAMINHO_LOG_RAIZ.path, "w", "utf-8"),
                        logging.FileHandler(self.CAMINHO_LOG_PERSISTENCIA.path, "w", "utf-8")):
            handler.addFilter(FileFilter(self.__nome))
            handler.setFormatter(
                JsonFormatter(self.IDENTIFICADOR_LOGGER,
                              self.CAMINHO_LOG_RAIZ.parente.string)
            )
            root.addHandler(handler)

        # Adicionar STDOUT Handler
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(StdoutFilter(self.__nome))
        handler.setFormatter(
            JsonFormatter(self.IDENTIFICADOR_LOGGER,
                          self.CAMINHO_LOG_RAIZ.parente.string,
                          adicionar_file=False)
        )
        root.addHandler(handler)

        return self

    def __limpeza_diretorio_persistencia (self) -> None:
        """Limpar os logs no `CAMINHO_DIRETORIO_PERSISTENCIA` que ultrapassaram a data limite
        - Registrado para executar ao fim do Python automaticamente
        - `Default:` 14 dias"""
        dias = bot.configfile.obter_opcao_ou("logger", "dias_persistencia", 14)
        limite = Timedelta(days=dias)

        for caminho in self.CAMINHO_DIRETORIO_PERSISTENCIA:
            if not caminho.arquivo(): continue
            data = Datetime.strptime(caminho.nome, self.FORMATO_NOME_LOG_PERSISTENCIA)\
                           .astimezone(TIMEZONE_BRT)
            if self.INICIALIZACAO_PACOTE - data < limite: break
            caminho.apagar_arquivo()

    def debug (self, mensagem: SupportsStr,
                     **extra: object) -> typing.Self:
        """Log nível `DEBUG`"""
        self.logger.debug(
            str(mensagem),
            stacklevel = 2,
            extra = { "extra": extra }
        )
        return self

    def informar (self, mensagem: SupportsStr,
                        **extra: object) -> typing.Self:
        """Log nível `INFO`"""
        self.logger.info(
            str(mensagem),
            stacklevel = 2,
            extra = { "extra": extra }
        )
        return self

    def alertar (self, mensagem: SupportsStr,
                       **extra: object) -> typing.Self:
        """Log nível `WARNING`
        - `Exception` capturada automaticamente, caso dentro do `except`"""
        self.logger.warning(
            str(mensagem),
            stacklevel = 2,
            extra = { "extra": extra },
            exc_info = erro if any(erro := sys.exc_info()) else None
        )
        return self

    def erro (self, mensagem: SupportsStr,
                    excecao: Exception | None = None,
                    **extra: object) -> typing.Self:
        """Log nível `ERROR`
        - `excecao=None` capturada automaticamente, caso esteja dentro do `except`"""
        self.logger.error(
            str(mensagem),
            stacklevel = 2,
            extra = { "extra": extra },
            exc_info = excecao or sys.exc_info()
        )
        return self

    def limpar_log_raiz (self) -> typing.Self:
        """Limpar o `CAMINHO_LOG_RAIZ`
        - Não afeta o `CAMINHO_DIRETORIO_PERSISTENCIA`"""
        root = self.logger.root
        if not root.handlers or not isinstance(root.handlers[0].formatter, JsonFormatter):
            return self

        handler = logging.FileHandler(self.CAMINHO_LOG_RAIZ.path, "w", "utf-8")
        handler.addFilter(FileFilter(self.__nome))
        handler.setFormatter(
            JsonFormatter(self.IDENTIFICADOR_LOGGER,
                          self.CAMINHO_LOG_RAIZ.parente.string)
        )

        root.handlers[0].close()
        root.handlers[0] = handler

        return self

    def obter_tracer (self, **extra: object) -> TracerLogger:
        """Obter o `TracerLogger` utilizado para realizar o rastreamento de um processo
        - `extra` as propriedades serão replicadas em todos os níveis do `Tracer`
        - Deve ser encerrado pelo `tracer.encerrar(status, mensagem)` ou utiizar com o `with` para o encerramento automático"""
        return TracerLogger(self.logger, extra)

    def tempo_execucao[R] (self, func: typing.Callable[P, R]) -> typing.Callable[P, R]: # type: ignore
        """Loggar o tempo de execução de uma função
        - Usar como decorador em uma função `@`"""
        @functools.wraps(func)
        def wrapper (*args: P.args, **kwargs: P.kwargs) -> R: # type: ignore
            cronometro, resultado = bot.tempo.Cronometro(), func(*args, **kwargs)
            tempo = bot.tempo.formatar_tempo_decorrido(decorrido := cronometro())
            self.informar(
                f"Função({ func.__name__ }) executada em {tempo}",
                nome_funcao = func.__name__,
                segundos = decorrido
            )
            return resultado
        return wrapper # type: ignore

logger = MainLogger("BOT")
"""Classe pré-configurada para criar, consultar e tratar os arquivos de log.  
Constante do logger com o `name=BOT`.  
Utilizar `logger.obter_logger(nome)` ou importar o `MainLogger(nome)` para criar uma instância com outro nome

#### Inicializar manualmente `logger.inicializar_logger()`
    - Stream para o `stdout`
    - Cria um LOG no diretório de execução para fácil acesso `CAMINHO_LOG_RAIZ`
    - Salva um LOG no diretório de persistência `CAMINHO_LOG_PERSISTENCIA`
    - Variáveis .ini `[logger] -> [dias_persistencia: 14, flag_debug: False]`"""

__all__ = ["logger", "MainLogger", "TracerLogger"]