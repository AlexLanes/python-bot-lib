# std
import re
from inspect import stack
from itertools import zip_longest
from unicodedata import normalize
from time import sleep, perf_counter
from typing import Callable, Iterable
# interno
from bot.tipagem import InfoStack


def aguardar_condicao (condicao: Callable[[], bool], timeout: int) -> bool:
    """Repetir a função `condição` por `timeout` segundos até que resulte em `True`
    - Retorna um `bool` indicando se a `condição` foi atendida
    - Exceções são ignoradas"""
    inicio = perf_counter()

    while perf_counter() - inicio < timeout:
        try:
            if condicao(): return True
            else: sleep(0.11)
        except: pass

    return False


def remover_acentuacao (string: str) -> str:
    """Remover a acentuação de uma string"""
    nfkd = normalize("NFKD", str(string))
    ascii = nfkd.encode("ASCII", "ignore")
    return ascii.decode("utf-8", "ignore")


def normalizar (string: str) -> str:
    """Strip, lower, replace espaços por underline, remoção de acentuação e remoção de caracteres != `a-zA-Z0-9_`"""
    string = re.sub(r"\s+", "_", string.strip().lower())
    string = remover_acentuacao(string)
    return re.sub(r"\W", "", string)


def obter_info_stack (index=1) -> InfoStack:
    """Obter informações presente no stack dos callers
    - `Default` Arquivo que chamou o info_stack()"""
    linha = stack()[index].lineno
    funcao = stack()[index].function
    filename = stack()[index].filename

    caminho, nome = filename.rsplit("\\", 1)
    caminho = f"{ caminho[0].upper() }{ caminho[1:] }" # forçar upper no primeiro char
    return InfoStack(nome, caminho, funcao, linha)


def index_melhor_match (texto: str, opcoes: Iterable[str]) -> int:
    """Encontrar o index da melhor opção nas `opcoes` que seja parecido com o `texto`
    - Se o index for -1, significa que nenhuma opção gerou um resultado satisfatório"""
    texto, scores = normalizar(texto), []
    for opcao in opcoes:
        opcao = normalizar(opcao)
        score = sum(1 if chars[0] == chars[1] else -1 for chars in zip_longest(texto, opcao))
        scores.append(score)
    
    score = max(scores)
    return scores.index(score) if score >= 1 else -1


__all__ = [
    "normalizar",
    "obter_info_stack",
    "aguardar_condicao",
    "remover_acentuacao",
    "index_melhor_match"
]
