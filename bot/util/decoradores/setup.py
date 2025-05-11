# std
import time, typing
import asyncio, cProfile, inspect, pstats
from multiprocessing.pool import ThreadPool
from multiprocessing.context import TimeoutError as Timeout
# interno
from ... import util, logger, database, sistema

P = typing.ParamSpec("P")

def timeout[R] (segundos: float) -> typing.Callable[[typing.Callable[P, R]], typing.Callable[P, R]]: # type: ignore
    """Executar a função por `segundos` até retornar ou `TimeoutError` caso ultrapasse o tempo"""
    def timeout (func: typing.Callable[P, R]) -> typing.Callable[P, R]:
        def timeout (*args: P.args, **kwargs: P.kwargs) -> R:

            mensagem = f"Função({func.__name__}) não finalizou sua execução no tempo configurado de {segundos} segundos e resultou em Timeout"
            try: return ThreadPool(1).apply_async(func, args, kwargs).get(segundos)
            except Timeout: logger.alertar(mensagem)
            raise TimeoutError(mensagem)

        return timeout
    return timeout

def retry[R] (
        *erro: type[Exception],
        tentativas: int = 3,
        segundos: int | float = 0.0,
        ignorar: tuple[type[Exception], ...] = (NotImplementedError,),
        on_error: typing.Callable[[tuple[typing.Any, ...], dict[str, typing.Any]], typing.Any] | None = None
    ) -> typing.Callable[[typing.Callable[P, R]], typing.Callable[P, R]]: # type: ignore
    """Realizar `tentativas` de se chamar uma função após algum dos `erro` e aguardar `segundos` até tentar novamente
    - `erro` especificar as exceções permitidas para retry. `(Default: Exception)`
    - `ignorar` exceções para não se aplicar o retry. `(Default: NotImplementedError)`
    - `on_error` uma função para ser executada após um erro.
        - Aceita 2 parâmetros `args, kwargs` com os argumentos que foram informados na chamada da função
    - `raise` na última tentativa com falha"""
    assert tentativas >= 1 and segundos >= 0.0, "O @retry espera tentativas >= 1 e segundos >= 0.0"
    erros = erro or (Exception,)

    def retry (func: typing.Callable[P, R]) -> typing.Callable[P, R]:
        nome_funcao = func.__name__

        def retry (*args: P.args, **kwargs: P.kwargs) -> R:
            for tentativa in range(1, tentativas + 1):
                try: return func(*args, **kwargs)

                except *ignorar as grupo_ignorado:
                    try: on_error(args, kwargs) if on_error else None
                    except Exception: pass
                    ultima_excecao = grupo_ignorado.exceptions[-1]
                    nome_excecao = type(ultima_excecao).__name__
                    ultima_excecao.add_note(f"Função({nome_funcao}) apresentou erro ao ser executada; Exceção '{nome_excecao}' não permitida a retentativa")
                    raise

                except *erros as grupo_excecoes:
                    try: on_error(args, kwargs) if on_error else None
                    except Exception: pass
                    ultima_excecao = grupo_excecoes.exceptions[-1]
                    mensagem_erro = type(ultima_excecao).__name__ + f"({ str(ultima_excecao).strip() })"
                    logger.alertar(f"Tentativa {tentativa}/{tentativas} de execução da função({nome_funcao}) resultou em erro\n\t{mensagem_erro}")
                    # sleep() não necessário na última tentativa
                    if tentativa < tentativas: time.sleep(segundos)
                    # lançar a exceção na última tentativa
                    else:
                        ultima_excecao.add_note(f"Foram realizadas {tentativas} tentativa(s) de execução da função({nome_funcao})")
                        raise

            # nunca
            raise

        return retry
    return retry

def tempo_execucao[R] (func: typing.Callable[P, R]) -> typing.Callable[P, R]: # type: ignore
    """Loggar o tempo de execução da função"""
    def tempo_execucao (*args: P.args, **kwargs: P.kwargs) -> R: # type: ignore
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

def async_run[R] (func: typing.Callable[P, R | typing.Coroutine[None, None, R]]) -> typing.Callable[P, R]: # type: ignore
    """Executar função async automaticamente como `asyncio.run()`"""
    def async_run (*args: P.args, **kwargs: P.kwargs) -> R: # type: ignore
        resultado = func(*args, **kwargs)
        funcao_async = inspect.iscoroutinefunction(func)
        return asyncio.run(resultado) if funcao_async else resultado # type: ignore
    return async_run

__all__ = [
    "retry",
    "timeout",
    "async_run",
    "tempo_execucao",
    "perfil_execucao",
]