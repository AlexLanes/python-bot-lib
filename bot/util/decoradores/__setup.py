# std
from pstats import Stats
from typing import Callable
from cProfile import Profile
from time import perf_counter
from multiprocessing.pool import ThreadPool
# interno
import bot


def setar_timeout (segundos: float):
    """Executar a função por `segundos` até retornar ou `multiprocessing.context.TimeoutError` caso ultrapasse o tempo
    - Função"""
    def setar_timeout (func: Callable):
        def setar_timeout (*args, **kwargs):
            return ThreadPool(1).apply_async(func, args, kwargs).get(segundos) 
        return setar_timeout
    return setar_timeout


def ignorar_excecoes (excecoes: list[Exception], default=None):
    """Igonorar `exceções` especificadas e retornar o `default` quando ignorado
    - Função"""
    def ignorar_excecoes (func: Callable):
        def ignorar_excecoes (*args, **kwargs):
            try: return func(*args, **kwargs)
            except Exception as erro: 
                if any(isinstance(erro, excecao) for excecao in excecoes): return default
                else: raise
        return ignorar_excecoes
    return ignorar_excecoes


def tempo_execucao (func: Callable):
    """Loggar o tempo de execução da função em segundos
    - Função"""
    def tempo_execucao (*args, **kwargs):
        inicio, resultado = perf_counter(), func(*args, **kwargs)
        bot.logger.informar(f"Função({ func.__name__ }) executada em {perf_counter() - inicio:.3f} segundos")
        return resultado
    return tempo_execucao


def perfil_execucao (func: Callable):
    """Loggar o perfil de execução da função
    - tempos acumulados menores de 0.01 segundos são excluídos
    - Função"""
    def perfil_execucao (*args, **kwargs):
        # Diretorio de execução atual para limpar o nome no dataframe
        cwd = bot.windows.diretorio_execucao().caminho
        cwd = f"{ cwd[0].lower() }{ cwd[1:] }"
        
        # Executar função com o profile ativo e gerar o report
        with Profile() as profile: resultado = func(*args, **kwargs)
        stats = Stats(profile).sort_stats(2).get_stats_profile()
        tempo = stats.total_tt
        stats = stats.func_profiles
        
        # Loggar o Dataframe com algumas opções de formatação
        kwargs = { "tbl_rows": 1000, "tbl_hide_dataframe_shape": True, "fmt_str_lengths": 1000, "tbl_hide_column_data_types": True }
        with bot.database.polars.Config(**kwargs):
            bot.logger.debug("\n" * 2 + 
                f"1 - Nome da função: { func.__name__ }\n" +
                f"2 - Tempo de execução: {tempo:.3f} segundos\n" +
                bot.database.polars.DataFrame({
                    "nome": [
                        funcao if stats[funcao].file_name == "~" 
                        else stats[funcao].file_name.removeprefix(cwd).lstrip("\\") + f":{ stats[funcao].line_number }({ funcao })"
                        for funcao in stats
                    ],
                    "tempo_acumulado": [stats[funcao].cumtime for funcao in stats],
                    "tempo_execucao": [stats[funcao].tottime for funcao in stats],
                    "chamadas": [stats[funcao].ncalls for funcao in stats]
                })
                .filter(bot.database.polars.col("tempo_acumulado") >= 0.01)
                .__str__() 
                + "\n"
            )
        return resultado
    return perfil_execucao


__all__ = [
    "setar_timeout",
    "tempo_execucao",
    "perfil_execucao",
    "ignorar_excecoes"
]
