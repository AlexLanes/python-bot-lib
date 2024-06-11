# std
import re
from unicodedata import normalize
from difflib import SequenceMatcher
from time import sleep, perf_counter
from typing import Callable, Iterable
# interno
from bot.tipagem import primitivo


def aguardar_condicao (condicao: Callable[[], bool], timeout: int, delay=0.1) -> bool:
    """Repetir a função `condição` por `timeout` segundos até que resulte em `True`
    - Retorna um `bool` indicando se a `condição` foi atendida
    - Exceções são ignoradas"""
    tempo = cronometro()

    while tempo() < timeout:
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


def index_texto (texto: str, opcoes: Iterable[str]) -> int:
    """Encontrar o index da melhor opção do `texto` nas `opcoes` fornecidas
    - Se o index for -1, significa que nenhuma opção gerou um resultado satisfatório"""
    # opção exata
    opcoes = list(opcoes)
    if texto in opcoes: return opcoes.index(texto)

    # opção normalizada
    texto = normalizar(texto)
    opcoes = [normalizar(opcao) for opcao in opcoes]
    if texto in opcoes: return opcoes.index(texto)

    # comparando similaridade dos caracteres
    # algorítimo `gestalt pattern matching`
    def calcular_similaridade (a: str, b: str) -> float:
        punicao_tamanho = abs(len(a) - len(b)) * 0.05
        return SequenceMatcher(None, a, b).ratio() - punicao_tamanho
    similaridades = [calcular_similaridade(texto, opcao) for opcao in opcoes]

    maior = max(similaridades)
    return similaridades.index(maior) if maior >= 0.6 else -1


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

    return " e ".join(tempos)


def transformar_tipo[T: primitivo] (valor: str, tipo: type[T]) -> T:
    """Fazer a transformação do `valor` para `type(tipo)`
    - Função genérica"""
    match str(tipo):
        case "<class 'str'>": return valor
        case "<class 'int'>" | "<class 'float'>": return tipo(valor)
        case "<class 'bool'>": return valor.lower().strip() == "true"
        case _: return None


def cronometro () -> Callable[[], float]:
    """Inicializa um cronômetro que retorna o tempo passado a cada chamada na função
    - Arredondado para 3 casas decimais"""
    inicio = perf_counter()
    return lambda: round(perf_counter() - inicio, 3)


__all__ = [
    "normalizar",
    "cronometro",
    "index_texto",
    "expandir_tempo",
    "transformar_tipo",
    "aguardar_condicao",
    "remover_acentuacao"
]
