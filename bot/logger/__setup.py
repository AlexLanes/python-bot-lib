# std
import logging
from sys import exc_info
# interno
from bot.util import info_stack


NOME_ARQUIVO = ".log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | id(%(process)d) | level(%(levelname)s) | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    filename=NOME_ARQUIVO,
    encoding="utf-8",
    filemode="w"
)


def debug (mensagem: str) -> None:
    """Log nível 'DEBUG'"""
    logging.debug(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }")

    
def informar (mensagem: str) -> None:
    """Log nível 'INFO'"""
    logging.info(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }")


def alertar (mensagem: str) -> None:
    """Log nível 'WARNING'"""
    logging.warning(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }")


def erro (mensagem: str) -> None:
    """Log nível 'ERROR'"""
    logging.error(f"arquivo({ info_stack(2).nome }) | função({ info_stack(2).funcao }) | linha({ info_stack(2).linha }) | { mensagem }", exc_info=exc_info())


__all__ = [
    "erro",
    "debug", 
    "alertar",
    "informar",
    "NOME_ARQUIVO"
]
