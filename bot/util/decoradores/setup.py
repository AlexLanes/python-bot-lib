# std
import time, asyncio, inspect, typing, pstats, cProfile
from multiprocessing.pool import ThreadPool
from multiprocessing.context import TimeoutError as Timeout
# interno
from ... import util, logger, database, sistema

P = typing.ParamSpec("P")

def timeout (segundos: float):
    """Executar a função por `segundos` até retornar ou `TimeoutError` caso ultrapasse o tempo"""
    def timeout (func: typing.Callable):
        def timeout (*args, **kwargs):
            mensagem = f"Função({func.__name__}) não finalizou sua execução no tempo configurado de {segundos} segundos e resultou em Timeout"
            try: return ThreadPool(1).apply_async(func, args, kwargs).get(segundos)
            except Timeout: logger.alertar(mensagem)
            raise TimeoutError(mensagem)
        return timeout
    return timeout

def retry (*erro: type[Exception],
           tentativas=3, segundos=5,
           ignorar: tuple[type[Exception], ...] = (NotImplementedError,)):
    """Realizar `tentativas` de se chamar uma função e, em caso de erro, aguardar `segundos` e tentar novamente
    - `erro` especificar as exceções permitidas para retry. `(Default: Exception)`
    - `ignorar` exceções para não se aplicar o retry. `(Default: RuntimeError)`
    - `raise` na última tentativa com falha"""
    erros = erro or (Exception,)
    assert tentativas >= 1 and segundos >= 1, "Tentativas e Segundos para o retry devem ser >= 1"
    def retry (func: typing.Callable):
        def retry (*args, **kwargs):

            nome_funcao = func.__name__
            for tentativa in range(1, tentativas + 1):
                try: return func(*args, **kwargs)
                except *ignorar as grupo_ignorado:
                    ultima_excecao = grupo_ignorado.exceptions[-1]
                    raise ultima_excecao from None
                except *erros as grupo_excecoes:
                    ultima_excecao = grupo_excecoes.exceptions[-1]
                    mensagem_erro = type(ultima_excecao).__name__ + f"({ str(ultima_excecao).strip() })"
                    logger.alertar(f"Tentativa {tentativa}/{tentativas} de execução da função({ nome_funcao }) resultou em erro\n\t{mensagem_erro}")
                    if tentativa < tentativas: time.sleep(segundos) # sleep() não necessário na última tentativa
                    else: # lançar a exceção na última tentativa
                        ultima_excecao.add_note(f"Foram realizadas {tentativas} tentativa(s) de execução da função({ nome_funcao })")
                        raise ultima_excecao

        return retry
    return retry

def tempo_execucao (func: typing.Callable):
    """Loggar o tempo de execução da função"""
    def tempo_execucao (*args, **kwargs):
        cronometro, resultado = util.cronometro(), func(*args, **kwargs)
        tempo = util.expandir_tempo(cronometro())
        logger.informar(f"Função({func.__name__}) executada em {tempo}")
        return resultado
    return tempo_execucao

def perfil_execucao (func: typing.Callable):
    """Loggar o perfil de execução da função
    - Tempos acumulados menores de 0.01 segundos são excluídos"""
    def perfil_execucao (*args, **kwargs):
        # Diretorio de execução atual para limpar o nome no dataframe
        cwd = sistema.Caminho.diretorio_execucao().string
        cwd = f"{cwd[0].lower()}{cwd[1:]}"

        # Executar função com o profile ativo e gerar o report
        with cProfile.Profile() as profile:
            resultado = func(*args, **kwargs)
        stats = pstats.Stats(profile).sort_stats(2).get_stats_profile()
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
            .filter(database.polars.col("tempo_acumulado") >= 0.001)
        )
        logger.informar("\n" * 2 + 
            f"1 - Nome da função: {func.__name__}\n" +
            f"2 - Tempo de execução: {tempo:.3f} segundos\n" +
            df + 
            "\n"
        )

        return resultado
    return perfil_execucao

def async_run[T] (func: typing.Callable[P, T | typing.Coroutine[None, None, T]]):
    """Executar função async automaticamente como `asyncio.run()`"""
    def async_run (*args: P.args, **kwargs: P.kwargs) -> T:
        resultado = func(*args, **kwargs)
        funcao_async = inspect.iscoroutinefunction(func)
        return asyncio.run(resultado) if funcao_async else resultado
    return async_run

__all__ = [
    "retry",
    "timeout",
    "async_run",
    "tempo_execucao",
    "perfil_execucao",
]