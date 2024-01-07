# std
import logging
from sys import exc_info
from datetime import datetime, timedelta
# interno
import bot


NOME_ARQUIVO_LOG = ".log"
CAMINHO_PASTA_LOGS = "./logs"
FORMATO_NOME_LOG = "%Y-%m-%dT%H-%M-%S.log"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | nome(%(name)s) | level(%(levelname)s) | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    filename=NOME_ARQUIVO_LOG,
    encoding="utf-8",
    filemode="w"
)


def extrair_stack () -> tuple[str, str, int]:
    """Extrair informações do stack para formatar a mensagem de log
    - `caminho, funcao, linha = extrair_stack()`"""
    stack, diretorio_execucao = bot.util.obter_info_stack(3), bot.windows.diretorio_execucao().caminho
    caminho = rf"{ stack.caminho.replace(diretorio_execucao, '') }\{ stack.nome }".lstrip("\\")
    return (caminho, stack.funcao, stack.linha)


def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    caminho, funcao, linha = extrair_stack()
    logging.debug(f"arquivo({ caminho }) | função({ funcao }) | linha({ linha }) | { mensagem }")

    
def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    caminho, funcao, linha = extrair_stack()
    logging.info(f"arquivo({ caminho }) | função({ funcao }) | linha({ linha }) | { mensagem }")


def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    caminho, funcao, linha = extrair_stack()
    logging.warning(f"arquivo({ caminho }) | função({ funcao }) | linha({ linha }) | { mensagem }")


def erro (mensagem: str) -> None:
    """Log nível 'ERROR'"""
    caminho, funcao, linha = extrair_stack()
    logging.error(f"arquivo({ caminho }) | função({ funcao }) | linha({ linha }) | { mensagem }", exc_info=exc_info())


def salvar_log (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS) -> None:
    """Salvar o arquivo log na pasta informada
    - o nome do arquivo é o datetime atual"""
    nome = datetime.now().strftime(FORMATO_NOME_LOG)
    caminho = bot.windows.path.abspath(caminho)
    if not bot.windows.path.exists(caminho): bot.windows.criar_pasta(caminho)
    bot.windows.copiar_arquivo(NOME_ARQUIVO_LOG, f"{ caminho }/{ nome }")


def limpar_logs (caminho: bot.tipagem.caminho = CAMINHO_PASTA_LOGS, limite = timedelta(weeks=2)) -> None:
    """Limpar os logs que ultrapassaram a data limite
    - espera que os logs tenham o nome no formato `FORMATO_NOME_LOG`"""
    agora = datetime.now().replace(microsecond=0)
    caminho = bot.windows.path.abspath(caminho)
    if not bot.windows.path.exists(caminho): return
    for arquivo in bot.windows.listar_diretorio(caminho).arquivos:
        nome = bot.windows.path.basename(arquivo)
        data = datetime.strptime(nome, FORMATO_NOME_LOG)
        if agora - data > limite: bot.windows.apagar_arquivo(arquivo)


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
