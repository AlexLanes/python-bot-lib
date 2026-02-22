# std
import typing
# interno
import bot
from bot.tempo.cronometro import Cronometro

class Timeout:
    """Classe para se observar o tempo de execução e lançar `TimeoutError`
    - Modificar `mensagem` para alterar a mensagem padrão ao lançar o erro
    - Utilizar `cronometro.resetar()` para reiniciar o tempo

    - Utilizar os métodos `horas, minutos, segundos` para adicionar tempo
    ```python
    timeout = Timeout().horas(1).minutos(30)
    timeout = Timeout().segundos(120)
    ```

    - Utilizar `timeout.expirado()` para checar se o tempo de execução foi maior que o esperado
    ```python
    while not timeout.expirado(): ...
    expirou = timeout.expirado()
    ```

    - Utilizar `timeout.pendente()` para checar se não expirou ou `TimeoutError` caso expirado
    ```python
    while timeout.pendente(): ...
    ```
    """

    limite: float
    """Limite em segundos para o `Timeout`"""
    cronometro: Cronometro
    mensagem = "Tempo de execução maior que o esperado"

    def __init__ (self, mensagem: str | None = None) -> None:
        self.limite = 0.0
        self.cronometro = Cronometro()
        self.mensagem = mensagem or self.mensagem

    def __repr__ (self) -> str:
        return f"<Timeout de {self.limite} segundo(s)>"

    def resetar (self) -> typing.Self:
        """Resetar o início do cronômetro
        - Permanece com o tempo de timeout adicionado"""
        self.cronometro.resetar()
        return self

    def horas (self, h: float) -> typing.Self:
        """Adicionar `h` horas no timeout"""
        self.limite += h * 3600
        return self

    def minutos (self, m: float) -> typing.Self:
        """Adicionar `m` minutos no timeout"""
        self.limite += m * 60
        return self

    def segundos (self, s: float) -> typing.Self:
        """Adicionar `s` segundos no timeout"""
        self.limite += s
        return self

    def expirado (self) -> bool:
        """Checar se o tempo decorrido ultrapassou o tempo esperado"""
        return self.cronometro >= self.limite

    def pendente (self) -> typing.Literal[True]:
        """Checar se o tempo decorrido ultrapassou o tempo esperado
        - Retorna `True` caso não expirado
        - Lança `TimeoutError` com mensagem caso expirado"""
        if not self.expirado():
            return True

        erro = TimeoutError(self.mensagem)
        erro.add_note(f"Tempo esperado: {bot.tempo.formatar_tempo_decorrido(self.limite)}")
        erro.add_note(f"Tempo decorrido: {self.cronometro.decorrido_formatado}")
        raise erro
