# std
from time import sleep
from pstats import Stats
from typing import Callable
from cProfile import Profile
from multiprocessing.pool import ThreadPool
from multiprocessing.context import TimeoutError as Timeout
# interno
from ... import util, logger, database, estruturas

def timeout (segundos: float):
    """Executar a função por `segundos` até retornar ou `TimeoutError` caso ultrapasse o tempo
    - Função"""
    def timeout (func: Callable):
        def timeout (*args, **kwargs):
            mensagem = f"Função({func.__name__}) não finalizou sua execução no tempo configurado de {segundos} segundos e resultou em Timeout"
            try: return ThreadPool(1).apply_async(func, args, kwargs).get(segundos)
            except Timeout: logger.alertar(mensagem)
            raise TimeoutError(mensagem)
        return timeout
    return timeout

def retry (tentativas = 3,
           segundos = 5,
           *erro: Exception):
    """Realizar `tentativas` de se chamar uma função e, em caso de erro, aguardar `segundos` e tentar novamente
    - `erro` especificar quais são as `Exception` permitidas para retry
    - `raise` na última tentativa com falha
    - Função"""
    erro = erro or (Exception,)
    assert tentativas >= 1 and segundos >= 1, "Tentativas e Segundos para o retry devem ser >= 1"
    def retry (func: Callable):
        def retry (*args, **kwargs):

            for tentativa in range(1, tentativas + 1):
                try: return func(*args, **kwargs)
                except *erro as e:
                    excecao, *_ = map(repr, e.exceptions)
                    logger.alertar(f"""Tentativa {tentativa}/{tentativas} de execução da função({func.__name__}) resultou em erro\n\t{excecao}""")
                    if tentativa < tentativas: sleep(segundos) # sleep() não necessário na última tentativa
                    else: # lançar a exceção na última tentativa
                        e.add_note(f"Foram realizadas {tentativas} tentativa(s) de execução da função({func.__name__})")
                        raise

        return retry
    return retry

def tempo_execucao (func: Callable):
    """Loggar o tempo de execução da função
    - Função"""
    def tempo_execucao (*args, **kwargs):
        cronometro, resultado = util.cronometro(), func(*args, **kwargs)
        tempo = util.expandir_tempo(cronometro())
        logger.informar(f"Função({func.__name__}) executada em {tempo}")
        return resultado
    return tempo_execucao

def perfil_execucao (func: Callable):
    """Loggar o perfil de execução da função
    - Tempos acumulados menores de 0.01 segundos são excluídos
    - Função"""
    def perfil_execucao (*args, **kwargs):
        # Diretorio de execução atual para limpar o nome no dataframe
        cwd = estruturas.Caminho.diretorio_execucao().string
        cwd = f"{cwd[0].lower()}{cwd[1:]}"

        # Executar função com o profile ativo e gerar o report
        with Profile() as profile: resultado = func(*args, **kwargs)
        stats = Stats(profile).sort_stats(2).get_stats_profile()
        tempo = stats.total_tt
        stats = stats.func_profiles

        # Loggar o Dataframe com algumas opções de formatação
        df = database.formatar_dataframe(
            database.polars.DataFrame({
                "nome": (
                    funcao if stats[funcao].file_name == "~" 
                    else stats[funcao].file_name.removeprefix(cwd).lstrip("\\") + f":{stats[funcao].line_number}({funcao})"
                    for funcao in stats
                ),
                "tempo_acumulado": (stats[funcao].cumtime for funcao in stats),
                "tempo_execucao": (stats[funcao].tottime for funcao in stats),
                "chamadas": (stats[funcao].ncalls for funcao in stats)
            })
            .filter(database.polars.col("tempo_acumulado") >= 0.01)
        )
        logger.informar("\n" * 2 + 
            f"1 - Nome da função: {func.__name__}\n" +
            f"2 - Tempo de execução: {tempo:.3f} segundos\n" +
            df + 
            "\n"
        )

        return resultado
    return perfil_execucao

__all__ = [
    "retry",
    "timeout",
    "tempo_execucao",
    "perfil_execucao",
]