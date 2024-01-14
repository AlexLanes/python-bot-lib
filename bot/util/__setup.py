# std
import re
from pstats import Stats
from inspect import stack
from typing import Callable
from cProfile import Profile
from itertools import zip_longest
from unicodedata import normalize
from time import sleep, perf_counter
from multiprocessing.pool import ThreadPool
# interno
import bot
from bot.tipagem import InfoStack


def setar_timeout (segundos: float):
    """Decorator\n-\nExecutar a função por `segundos` segundos até retornar ou `TimeoutError`"""
    def decorator (func: Callable):
        def wrapper (*args, **kwargs):
            return ThreadPool(1).apply_async(func, args, kwargs).get(segundos) 
        return wrapper
    return decorator


def tempo_execucao (func: Callable):
    """Decorator\n-\nLoggar o tempo de execução da função em segundos"""
    def tempo_execucao (*args, **kwargs):
        inicio, resultado = perf_counter(), func(*args, **kwargs)
        bot.logger.informar(f"Função({ func.__name__ }) executada em {perf_counter() - inicio:.2f} segundos")
        return resultado
    return tempo_execucao


def perfil_execucao (func: Callable):
    """Decorator\n-\nLoggar o perfil de execução da função com tempos em segundos"""
    def perfil_execucao (*args, **kwargs):
        cwd = bot.windows.diretorio_execucao().caminho
        cwd = f"{ cwd[0].lower() }{ cwd[1:] }"
        
        with Profile() as profile: resultado = func(*args, **kwargs)
        stats = Stats(profile).get_stats_profile().func_profiles

        df = bot.database.polars.DataFrame({
            "nome": [funcao if stats[funcao].file_name == "~" \
                    else stats[funcao].file_name.removeprefix(cwd).lstrip("\\") + f":{ stats[funcao].line_number }({ funcao })"
                    for funcao in stats],
            "tempo_acumulado": [stats[funcao].cumtime for funcao in stats],
            "tempo_execucao": [stats[funcao].tottime for funcao in stats],
            "chamadas": [stats[funcao].ncalls for funcao in stats]
        }) \
        .sort("tempo_acumulado", descending=True) \
        .filter(bot.database.polars.col("tempo_acumulado") >= 0.1)

        kwargs = { "tbl_rows": 1000, "fmt_str_lengths": 1000, "tbl_hide_dataframe_shape": True, "tbl_hide_column_data_types": True }
        with bot.database.polars.Config(**kwargs): bot.logger.debug("\n" + str(df))
        return resultado
    return perfil_execucao


def ignorar_excecoes (excecoes: list[Exception], default=None):
    """Decorator\n-\nIgonorar `exceções` especificadas e retornar o `default` quando ignorado"""
    def decorator (func: Callable):
        def wrapper (*args, **kwargs):
            try: return func(*args, **kwargs)
            except Exception as erro: 
                if any(isinstance(erro, excecao) for excecao in excecoes): return default
                else: raise
        return wrapper
    return decorator


def aguardar_condicao (condicao: Callable[[], bool], timeout: int, erro: Exception = None) -> bool | Exception:
    """Repetir a função `condicao` por `timeout` segundos até que resulte em `True`
    - `False` se a condição não for atendida após `timeout` ou `erro` se for informado"""
    inicio = perf_counter()
    while perf_counter() - inicio < timeout:
        if condicao(): return True
        else: sleep(0.11)
    if erro != None: raise erro
    return False


def remover_acentuacao (string: str) -> str:
    """Remover a acentuação de uma string"""
    nfkd = normalize("NFKD", str(string))
    ascii = nfkd.encode("ASCII", "ignore")
    return ascii.decode("utf-8", "ignore")


def normalizar (string: str) -> str:
    """Strip, lower, replace espaços por underline e remoção de acentuação"""
    string = str(string).strip().lower()
    string = re.sub(r"\s+", "_", string)
    return remover_acentuacao(string)


def obter_info_stack (index=1) -> InfoStack:
    """Obter informações presente no stack dos callers
    - `Default` Arquivo que chamou o info_stack()"""
    linha = stack()[index].lineno
    funcao = stack()[index].function
    filename = stack()[index].filename

    caminho, nome = filename.rsplit("\\", 1)
    caminho = f"{ caminho[0].upper() }{ caminho[1:] }" # forçar upper no primeiro char
    return InfoStack(nome, caminho, funcao, linha)


def index_melhor_match (texto: str, opcoes: list[str]) -> int:
    """Encontrar o index da melhor opção nas `opcoes` que seja parecido com o `texto`
    - Se o index for -1, significa que nenhuma opção gerou um resultado satisfatório"""
    assert len(opcoes) >= 1, f"Nenhuma opção informada para o texto '{ texto }'"

    texto, scores = normalizar(texto), []
    for opcao in opcoes:
        opcao = normalizar(opcao)
        score = sum(1 if chars[0] == chars[1] else -1 for chars in zip_longest(texto, opcao))
        scores.append(score)
    
    score = max(scores)
    return scores.index(score) if score >= 1 else -1


__all__ = [
    "normalizar",
    "setar_timeout",
    "tempo_execucao",
    "perfil_execucao",
    "ignorar_excecoes",
    "obter_info_stack",
    "aguardar_condicao",
    "remover_acentuacao",
    "index_melhor_match"
]
