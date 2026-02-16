# std
import typing, functools
import cProfile, pstats
import asyncio, inspect
# interno
import bot

P = typing.ParamSpec("P")

def transformar_tipo[T: bot.tipagem.primitivo] (valor: str, tipo: type[T]) -> T:
    """Fazer a transformação do `valor` para `type(tipo)`
    - Função genérica"""
    match tipo():
        case bool():    return valor.lower().strip() == "true" # type: ignore
        case float():   return float(valor) # type: ignore
        case int():     return int(valor) # type: ignore
        case _:         return valor # type: ignore

def perfil_execucao[R] (func: typing.Callable[P, R]) -> typing.Callable[P, R]: # type: ignore
    """Realizar um `print()` do perfil de execução da função
    - Tempos acumulados menores de 0.01 segundos são excluídos
    - Usar como decorador em uma função `@`"""
    @functools.wraps(func)
    def perfil_execucao (*args, **kwargs) -> R:
        # Diretorio de execução atual para limpar o nome no dataframe
        cwd = bot.sistema.Caminho.diretorio_execucao().string
        cwd = f"{cwd[0].lower()}{cwd[1:]}"

        # Executar função com o profile ativo e gerar o report
        with cProfile.Profile() as profile:
            resultado = func(*args, **kwargs)
        stats = pstats.Stats(profile).sort_stats(2).get_stats_profile()
        tempo = stats.total_tt
        stats = stats.func_profiles

        # Loggar o Dataframe com algumas opções de formatação
        df = bot.database.formatar_dataframe(
            bot.database.polars.DataFrame({
                "nome": (
                    funcao if stats[funcao].file_name == "~" 
                    else stats[funcao].file_name.removeprefix(cwd).lstrip("\\") + f":{stats[funcao].line_number}({funcao})"
                    for funcao in stats
                ),
                "tempo_acumulado": (stats[funcao].cumtime for funcao in stats),
                "tempo_execucao": (stats[funcao].tottime for funcao in stats),
                "chamadas": (stats[funcao].ncalls for funcao in stats)
            })
            .filter(bot.database.polars.col("tempo_acumulado") >= 0.001)
        )

        print("\n" * 2 + 
            f"1 - Nome da função: {func.__name__}\n" +
            f"2 - Tempo de execução: {tempo:.3f} segundos\n" +
            df + 
            "\n"
        )

        return resultado
    return perfil_execucao

def async_run[R] (func: typing.Callable[P, R | typing.Coroutine[None, None, R]]) -> typing.Callable[P, R]: # type: ignore
    """Executar funções `async` automaticamente com o `asyncio.run()`
    - Usar como decorador em uma função `@`"""
    @functools.wraps(func)
    def async_run (*args: P.args, **kwargs: P.kwargs) -> R: # type: ignore
        resultado = func(*args, **kwargs)
        funcao_async = inspect.iscoroutinefunction(func)
        return asyncio.run(resultado) if funcao_async else resultado # type: ignore
    return async_run # type: ignore

__all__ = [
    "async_run",
    "perfil_execucao",
    "transformar_tipo",
]