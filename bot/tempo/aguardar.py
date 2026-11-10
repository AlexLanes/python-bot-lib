# std
import time, typing
# interno
import bot
from bot.tipagem import SupportsBool

class ResultadoAguardar[T]:

    ok: bool

    def __init__ (self, ok: bool, valor: T) -> None:
        self.ok = ok
        self.__valor = valor

    def __repr__ (self) -> str:
        return f"<ResultadoEsperar {"sucesso" if self.ok else "erro"}>"

    def __bool__ (self) -> bool:
        return self.ok

    def valor (self) -> T:
        """Obter o `valor` do resultado
        - Necessário validar se o resultado é de sucesso"""
        if not self.ok:
            raise ValueError("Tentado obter o valor de um resultado sem sucesso")
        return self.__valor

    def valor_ou[D] (self, default: D) -> T | D:
        """Obter o valor do resultado ou `default` caso sem sucesso"""
        return self.__valor if self.ok else default

def aguardar[T: SupportsBool] (condicao: typing.Callable[[], T],
                               timeout: int | float,
                               delay: int | float = 0.01,
                               comparador: typing.Callable[[T], bool] | None = None) -> ResultadoAguardar[T]:
    """Repetir a função `condição`, aguardando por `timeout` segundos, até que resulte em `True`
    - Exceções são ignoradas
    - `comparador` default checado se `bool(resultado) == True`
    - Retorna uma classe especializada para se checar sucesso e obter o valor retornado
    ### Exemplo
    ```
    import bot, random

    def acima_95 () -> int:
        n = random.randint(0, 100)
        assert n > 95
        return n

    #-- Simplificado --#
    resultado = bot.tempo.aguardar(acima_95, timeout=2, delay=0.1)
    if resultado: print("Sucesso", resultado.valor())
    else: print("Falha")

    #-- Com comparador --#    
    resultado = bot.tempo.aguardar(
        lambda: random.randint(0, 100),
        timeout = 2, delay = 0.1,
        comparador = lambda n: n > 95
    )
    if resultado.ok: print("Sucesso", resultado.valor())
    else: print("Falha")
    ```"""
    cronometro = bot.tempo.Cronometro()
    comparador = comparador or (lambda x: bool(x))

    while cronometro < timeout:
        try:
            valor = condicao()
            if comparador(valor):
                return ResultadoAguardar(ok=True, valor=valor)

        except Exception: pass
        time.sleep(delay)

    return ResultadoAguardar(ok=False, valor=None) # type: ignore

__all__ = ["aguardar"]