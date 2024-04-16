# std
from time import sleep
from pstats import Stats
from typing import Callable
from cProfile import Profile
from multiprocessing.pool import ThreadPool
from multiprocessing.context import TimeoutError as Timeout
# interno
import bot


def setar_timeout (segundos: float):
    """Executar a função por `segundos` até retornar ou `TimeoutError` caso ultrapasse o tempo
    - Função"""
    def setar_timeout (func: Callable):
        def setar_timeout (*args, **kwargs):
            mensagem = f"Função({func.__name__}) não finalizou sua execução no tempo configurado de {segundos} segundos e resultou em Timeout"
            try: return ThreadPool(1).apply_async(func, args, kwargs).get(segundos)
            except Timeout: bot.logger.alertar(mensagem)
            raise TimeoutError(mensagem)
        return setar_timeout
    return setar_timeout


def retry (tentativas=3, segundos=10):
    """Realizar `tentativas` de se chamar uma função, aguardar `segundos` e tentar novamente em caso de erro
    - Lança a exceção na última tentativa com falha
    - Função"""
    assert tentativas >= 1 and segundos >= 1, "Tentativas e Segundos para o retry deve ser >= 1"
    def retry (func: Callable):
        def retry (*args, **kwargs):

            for tentativa in range(1, tentativas + 1):
                try: return func(*args, **kwargs)
                except Exception as erro:
                    bot.logger.alertar(f"Tentativa {tentativa}/{tentativas} de execução da função({func.__name__}) resultou em erro\n\t{erro}")
                    if tentativa < tentativas: sleep(segundos) # sleep() não necessário na última tentativa
                    else: # lançar a exceção da última tentativa
                        erro.add_note(f"Foram realizadas {tentativas} tentativa(s) de execução na função({func.__name__})")
                        raise

        return retry
    return retry


def tempo_execucao (func: Callable):
    """Loggar o tempo de execução da função
    - Função"""
    def tempo_execucao (*args, **kwargs):
        cronometro, resultado = bot.util.cronometro(), func(*args, **kwargs)
        tempo = bot.util.expandir_tempo(cronometro())
        bot.logger.informar(f"Função({func.__name__}) executada em {tempo}")
        return resultado
    return tempo_execucao


def perfil_execucao (func: Callable):
    """Loggar o perfil de execução da função
    - tempos acumulados menores de 0.1 segundos são excluídos
    - Função"""
    def perfil_execucao (*args, **kwargs):
        # Diretorio de execução atual para limpar o nome no dataframe
        cwd = bot.windows.diretorio_execucao().caminho
        cwd = f"{cwd[0].lower()}{cwd[1:]}"
        
        # Executar função com o profile ativo e gerar o report
        with Profile() as profile: resultado = func(*args, **kwargs)
        stats = Stats(profile).sort_stats(2).get_stats_profile()
        tempo = stats.total_tt
        stats = stats.func_profiles
        
        # Loggar o Dataframe com algumas opções de formatação
        kwargs = { "tbl_rows": 1000, "tbl_hide_dataframe_shape": True, "fmt_str_lengths": 1000, "tbl_hide_column_data_types": True }
        with bot.database.polars.Config(**kwargs):
            bot.logger.debug("\n" * 2 + 
                f"1 - Nome da função: {func.__name__}\n" +
                f"2 - Tempo de execução: {tempo:.3f} segundos\n" +
                bot.database.polars.DataFrame({
                    "nome": [
                        funcao if stats[funcao].file_name == "~" 
                        else stats[funcao].file_name.removeprefix(cwd).lstrip("\\") + f":{stats[funcao].line_number}({funcao})"
                        for funcao in stats
                    ],
                    "tempo_acumulado": [stats[funcao].cumtime for funcao in stats],
                    "tempo_execucao": [stats[funcao].tottime for funcao in stats],
                    "chamadas": [stats[funcao].ncalls for funcao in stats]
                })
                .filter(bot.database.polars.col("tempo_acumulado") >= 0.1)
                .__str__() 
                + "\n"
            )
        return resultado
    return perfil_execucao


__all__ = [
    "retry",
    "setar_timeout",
    "tempo_execucao",
    "perfil_execucao",
]
