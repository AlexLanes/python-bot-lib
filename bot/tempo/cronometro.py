# std
import time, typing

class Cronometro:
    """Cronometrar o tempo decorrido
    - `precisao` para setar a precisão decimal ao se obter o tempo decorrido
    - `mensagem_timeout` para alterar a mensagem de timeout padrão definida
    - Utilizar `cronometro()` ou `cronometro.tempo_decorrido` para se obter o tempo decorrido em `segundos`
    - Comparadores aceitos `< <= > >=` na variável do `cronometro`
    - Utilizar `cronometro.timeout(...)` para checar por tempo de execução maior que o esperado"""

    epoch: float
    precisao: int
    mensagem_timeout = "Cronômetro resultou em tempo de execução maior que o esperado"

    def __init__ (self, precisao: int = 3,
                        mensagem_timeout: str | None = None) -> None:
        self.precisao = precisao
        self.epoch = round(time.perf_counter(), precisao)
        if mensagem_timeout:
            self.mensagem_timeout = mensagem_timeout

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

    def com_precisao (self, precisao: int) -> typing.Self:
        """Alterar `precisao` do cronômero"""
        self.precisao = precisao
        return self

    def timeout (self, *, horas:    int | float = 0,
                          minutos:  int | float = 0,
                          segundos: int | float = 0) -> typing.Self:
        """Checar se o tempo decorrido for `>` que o informado
        - Lança `TimeoutError` com mensagem de timeout pré-definida"""
        limite = round((horas * 3600) + (minutos * 60) + segundos, self.precisao)
        assert limite > 0.0, "Tempo de timeout do cronômetro deve ser positivo"

        if self.tempo_decorrido > limite:
            erro = TimeoutError(self.mensagem_timeout)
            erro.add_note(f"Tempo esperado: {horas} horas, {minutos} minutos e {segundos} segundos")
            raise erro

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
