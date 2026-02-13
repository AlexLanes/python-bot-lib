# std
import time, typing

class Cronometro:
    """Cronometrar o tempo decorrido
    - `precisao` para setar a precisão decimal ao se obter o tempo decorrido
    - Utilizar `cronometro()` ou `cronometro.tempo_decorrido` para se obter o tempo decorrido em `segundos`
    - Comparadores aceitos `< <= > >=` na variável do `cronometro`"""

    epoch: float
    precisao: int

    def __init__ (self, precisao: int = 3) -> None:
        self.precisao = precisao
        self.epoch = round(time.perf_counter(), precisao)

    def __repr__ (self) -> str:
        return f"<Cronometro decorrido='{self()}'>"

    def __call__ (self) -> float:
        delta = time.perf_counter() - self.epoch
        return abs(round(delta, self.precisao))

    @property
    def tempo_decorrido (self) -> float:
        """Tempo decorrido em segundos"""
        return self()

    def resetar (self) -> typing.Self:
        """Resetar o cronômetro"""
        self.epoch = abs(round(time.perf_counter(), self.precisao))
        return self

    def __lt__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch < other.epoch
        if isinstance(other, (int, float)):
            return self.tempo_decorrido < other
        return NotImplemented

    def __le__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch <= other.epoch
        if isinstance(other, (int, float)):
            return self.tempo_decorrido <= other
        return NotImplemented

    def __gt__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch > other.epoch
        if isinstance(other, (int, float)):
            return self.tempo_decorrido > other
        return NotImplemented

    def __ge__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch >= other.epoch
        if isinstance(other, (int, float)):
            return self.tempo_decorrido >= other
        return NotImplemented
