# std
import time, typing
# interno
import bot

class Cronometro:
    """Cronometrar o tempo decorrido
    - `precisao` ou `cronometro.com_precisao()` para setar a precisão decimal ao se obter o tempo decorrido
    - Utilizar `cronometro()` ou `cronometro.decorrido` para se obter o tempo decorrido em `segundos`
    - Utilizar `cronometro.resetar()` para reiniciar o tempo
    - Comparadores aceitos `< <= > >=` na variável do `cronometro`"""

    epoch:          float
    precisao:       int
    epoch_parcial:  float

    def __init__ (self, precisao: int = 3) -> None:
        self.precisao = precisao
        self.epoch = self.epoch_parcial = round(time.perf_counter(), precisao)

    def __repr__ (self) -> str:
        return f"<Cronometro decorrido='{self()}'>"

    def __call__ (self) -> float:
        delta = time.perf_counter() - self.epoch
        return abs(round(delta, self.precisao))

    @property
    def decorrido (self) -> float:
        """Tempo decorrido em segundos"""
        return self()

    @property
    def decorrido_formatado (self) -> str:
        """Formatar o tempo decorrido para as duas maiores unidades de grandeza
        - Horas
        - Minutos
        - Segundos
        - Milissegundos"""
        return bot.tempo.formatar_tempo_decorrido(self)

    def parcial (self) -> float:
        """Registrar uma volta parcial desde a última ou do começo, caso seja a primeira
        - Retornado o tempo decorrido parcial da volta"""
        agora = time.perf_counter()
        delta = agora - self.epoch_parcial
        self.epoch_parcial = agora
        return abs(round(delta, self.precisao))

    def resetar (self) -> typing.Self:
        """Resetar o cronômetro"""
        self.epoch = self.epoch_parcial = abs(round(time.perf_counter(), self.precisao))
        return self

    def com_precisao (self, precisao: int) -> typing.Self:
        """Alterar `precisao` do cronômero"""
        self.precisao = precisao
        return self

    def __lt__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch < other.epoch
        if isinstance(other, (int, float)):
            return self.decorrido < other
        return NotImplemented

    def __le__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch <= other.epoch
        if isinstance(other, (int, float)):
            return self.decorrido <= other
        return NotImplemented

    def __gt__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch > other.epoch
        if isinstance(other, (int, float)):
            return self.decorrido > other
        return NotImplemented

    def __ge__ (self, other) -> bool:
        if isinstance(other, Cronometro):
            return self.epoch >= other.epoch
        if isinstance(other, (int, float)):
            return self.decorrido >= other
        return NotImplemented
