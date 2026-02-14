# std
import contextlib
from time import sleep
from typing import Generator, Self
# interno
from .win_api import traduzir_tecla, send_input_tecla_api
from bot.tipagem import char, BOTOES_TECLADO

class Teclado:
    """Classe de controle do teclado
    - Alterar constantes `DELAY_...` para modificar tempo de espera após ação"""

    DELAY_APERTAR    = 0.1
    DELAY_DIGITAR    = 0.02
    DELAY_ATALHO     = 0.05
    DELAY_PRESSIONAR = 0.05

    def __repr__ (self) -> str:
        return "<bot.Teclado>"

    def apertar (self, *teclas: BOTOES_TECLADO | char) -> Self:
        """Pressionar e soltar as `teclas` uma vez"""
        try:
            for tecla in teclas:
                unicode, codigos = traduzir_tecla(tecla)
                for codigo in codigos:
                    send_input_tecla_api(codigo, pressionar=True,  unicode=unicode)
                    send_input_tecla_api(codigo, pressionar=False, unicode=unicode)

                sleep(self.DELAY_APERTAR)

        except Exception as erro:
            raise Exception(f"Erro ao apertar teclas {teclas}: {erro}")

        return self

    def digitar (self, texto: str) -> Self:
        """Digitar os caracteres no `texto`"""
        teclas_unicode = dict[str, tuple[bool, list[int]]]()

        for char in texto:
            if char not in teclas_unicode:
                teclas_unicode[char] = traduzir_tecla(char)

            unicode, codigos = teclas_unicode[char]
            for codigo in codigos:
                send_input_tecla_api(codigo, pressionar=True,  unicode=unicode)
                send_input_tecla_api(codigo, pressionar=False, unicode=unicode)

            sleep(self.DELAY_DIGITAR)

        return self

    def atalho (self, *teclas: BOTOES_TECLADO | char) -> Self:
        """Pressionar as `teclas` sequencialmente e soltá-las em ordem reversa"""
        codigos_teclas = [
            traduzir_tecla(tecla, virtual=True)
            for tecla in teclas
        ]

        # Pressionar
        for unicode, codigos in codigos_teclas:
            for codigo in codigos:
                send_input_tecla_api(codigo, pressionar=True, unicode=unicode)
            sleep(self.DELAY_ATALHO)

        # Soltar
        for unicode, codigos in reversed(codigos_teclas):
            for codigo in reversed(codigos):
                send_input_tecla_api(codigo, pressionar=False, unicode=unicode)
            sleep(self.DELAY_ATALHO)

        return self

    @contextlib.contextmanager
    def pressionar (self, *teclas: BOTOES_TECLADO | char) -> Generator[Self, None, None]:
        """Pressionar as `teclas` e soltar ao sair
        - Utilizar com o `with`"""
        pressionados = list[tuple[bool, int]]()

        # Pressionar e yield
        try:
            for tecla in teclas:
                unicode, codigos = traduzir_tecla(tecla, virtual=True)

                for codigo in codigos:
                    send_input_tecla_api(codigo, pressionar=True, unicode=unicode)
                    pressionados.append((unicode, codigo))

                sleep(self.DELAY_PRESSIONAR)

            yield self

        # Soltar todas as teclas em ordem inversa
        finally:
            for unicode, codigo in reversed(pressionados):
                send_input_tecla_api(codigo, pressionar=False, unicode=unicode)

    def sleep (self, segundos: int | float = 1) -> Self:
        """Aguardar por `segundos` até continuar a execução"""
        sleep(segundos)
        return self

teclado = Teclado()
"""Classe de controle do teclado
- Alterar constantes `DELAY_...` para modificar tempo de espera após ação"""

__all__ = ["teclado"]