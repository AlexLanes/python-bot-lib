# std
import logging
from sys import exc_info
from datetime import datetime, timedelta
# interno
import bot


NOME_ARQUIVO_LOG = ".log"
CAMINHO_PASTA_LOGS = "./logs"
FORMATO_NOME_LOG = "%Y-%m-%dT%H-%M-%S.log"


logger = logging.getLogger("BOT")
logger.setLevel(logging.DEBUG)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    filename=NOME_ARQUIVO_LOG,
    encoding="utf-8",
    filemode="w"
)


def criar_mensagem_padrao (mensagem: str) -> str:
    """Extrair informações do stack para adicionar na mensagem de log"""
    stack, diretorio_execucao = bot.util.obter_info_stack(3), bot.windows.diretorio_execucao().caminho
    caminho = rf"{ stack.caminho.removeprefix(diretorio_execucao) }\{ stack.nome }".lstrip("\\")
    return f"arquivo({ caminho }) | função({ stack.funcao }) | linha({ stack.linha }) | { mensagem }"


def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    logger.debug(criar_mensagem_padrao(mensagem))


def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    logger.info(criar_mensagem_padrao(mensagem))


def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    logger.warning(criar_mensagem_padrao(mensagem))


def erro (mensagem: str) -> None:
    """Log nível 'ERROR'"""
    logger.error(criar_mensagem_padrao(mensagem), exc_info=exc_info())


def salvar_log (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS) -> None:
    """Salvar o arquivo log na pasta informada
    - o nome do arquivo é o datetime atual"""
    nome = datetime.now().strftime(FORMATO_NOME_LOG)
    caminho = bot.windows.caminho_absoluto(caminho)
    if not bot.windows.confirmar_caminho(caminho): bot.windows.criar_pasta(caminho)
    bot.windows.copiar_arquivo(NOME_ARQUIVO_LOG, f"{ caminho }/{ nome }")


def limpar_logs (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS, limite = timedelta(weeks=2)) -> None:
    """Limpar os logs que ultrapassaram a data limite
    - espera que os logs tenham o nome no formato `FORMATO_NOME_LOG`"""
    caminho = bot.windows.caminho_absoluto(caminho)
    if not bot.windows.confirmar_caminho(caminho): return
    for caminho_log in bot.windows.listar_diretorio(caminho).arquivos:
        nome = bot.windows.extrair_nome_base(caminho_log)
        data = datetime.strptime(nome, FORMATO_NOME_LOG)
        if datetime.now() - data > limite: bot.windows.apagar_arquivo(caminho_log)


__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "salvar_log",
    "limpar_logs",
    "NOME_ARQUIVO_LOG",
    "CAMINHO_PASTA_LOGS"
]
