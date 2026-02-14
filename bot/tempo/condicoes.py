# std
import time, typing
# interno
import bot

def aguardar (condicao: typing.Callable[[], bot.tipagem.SupportsBool],
              timeout: int | float,
              delay: int | float = 0.01) -> bool:
    """Repetir a função `condição`, aguardando por `timeout` segundos, até que resulte em `True`
    - Retorna um `bool` indicando se a `condição` foi atendida
    - Exceções são ignoradas"""
    cronometro = bot.tempo.Cronometro()

    while cronometro < timeout:
        try:
            if condicao(): return True
        except Exception: pass
        time.sleep(delay)

    return False

class ResultadoEsperar[T]:

    ok: bool

    def __init__ (self) -> None:
        self.ok = False

    def __repr__ (self) -> str:
        return f"<ResultadoEsperar {"sucesso" if self.ok else "erro"}>"

    def __bool__ (self) -> bool:
        return self.ok

    def valor (self) -> T:
        """Obter o `valor` do resultado
        - Necessário validar se o resultado é de sucesso"""
        if not self.ok:
            raise Exception(f"Tentado obter o valor de um resultado sem sucesso")
        return self._valor # type: ignore

    def valor_ou[D] (self, default: D) -> T | D:
        """Obter o valor do resultado ou `default` caso sem sucesso"""
        return self._valor if self.ok else default # type: ignore

def esperar[T] (func: typing.Callable[[], T],
                timeout: int | float,
                delay: int | float = 0.01,
                comparador: typing.Callable[[T], bool] | None = None) -> ResultadoEsperar[T]:
    """Repetir a função `func` para se obter o valor esperado no `comparador`
    - Exceções são ignoradas
    - Aguardado por `timeout` segundos, até o resultado ser `True` no `comparador`
    - `comparador` default checado se `bool(resultado) == True`
    - Retorna uma classe especializada para se checar sucesso e obter o valor"""
    comparador = comparador or (lambda x: bool(x))
    resultado = ResultadoEsperar[T]()
    cronometro = bot.tempo.Cronometro()

    while cronometro < timeout:
        try:
            valor = func()
            if not comparador(valor): continue

            resultado.ok = True
            setattr(resultado, "_valor", valor)
            break

        except Exception: pass
        time.sleep(delay)

    return resultado

__all__ = [
    "esperar",
    "aguardar",
]