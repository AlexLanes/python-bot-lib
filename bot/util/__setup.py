# std
import re
from itertools import zip_longest
from unicodedata import normalize
from time import sleep, perf_counter
from typing import Callable, Iterable


def aguardar_condicao (condicao: Callable[[], bool], timeout: int, delay=0.1) -> bool:
    """Repetir a função `condição` por `timeout` segundos até que resulte em `True`
    - Retorna um `bool` indicando se a `condição` foi atendida
    - Exceções são ignoradas"""
    inicio = perf_counter()

    while perf_counter() - inicio < timeout:
        try:
            if condicao(): return True
        except: pass
        sleep(delay)

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


def expandir_tempo (segundos: int | float) -> str:
    """Expandir a medida `segundos` para as duas primeiras unidades de grandeza
    - Hora, Minuto, Segundo ou Milissegundo"""
    if not segundos: return "0 segundos"
    tempos, segundos = [], round(segundos, 3)

    for nome, medida in [("hora", 60 ** 2), ("minuto", 60), ("segundo", 1), ("milissegundo", 0.001)]:
        if segundos < medida: continue
        tempos.append(f"{int(segundos / medida)} {nome}{"s" if segundos >= medida * 2 else ""}")
        segundos %= medida
        if len(tempos) == 2: break

    return " e ".join(tempo for tempo in tempos)


__all__ = [
    "normalizar",
    "expandir_tempo",
    "aguardar_condicao",
    "remover_acentuacao",
    "index_melhor_match"
]
