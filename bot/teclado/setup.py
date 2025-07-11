# std
from time import sleep
from atexit import register
from typing import Any, Callable, Iterable
# interno
from .. import tipagem
# externo
from pynput.keyboard import Controller, Key, Listener

TECLADO = Controller()
CALLBACKS: dict[str, Callable[[], None]] = {}

def apertar_tecla (tecla: tipagem.BOTOES_TECLADO | tipagem.char, quantidade=1, delay=0.1) -> None:
    """Apertar e soltar uma tecla `qtd` vezes
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    t = tecla if len(tecla) == 1 else Key[tecla]
    for _ in range(max(quantidade, 1)):
        TECLADO.tap(t)
        sleep(delay)

def atalho_teclado (teclas: Iterable[tipagem.BOTOES_TECLADO | tipagem.char], delay=0.5) -> None:
    """Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    t = [
        tecla if len(tecla) == 1 else Key[tecla]
        for tecla in teclas
    ]
    for tecla in t: TECLADO.press(tecla) # pressionar
    for tecla in reversed(t): TECLADO.release(tecla) # soltar
    sleep(delay)

def digitar_teclado (texto: str, delay=0.05) -> None:
    """Digitar o texto pressionando cada tecla do texto e soltando em seguida"""
    for char in texto:
        TECLADO.type(char)
        sleep(delay)

def observar_tecla (tecla: tipagem.BOTOES_TECLADO | tipagem.char, callback: Callable[[], Any]) -> None:
    """Observar quando a `tecla` é apertada e chamar o `callback`
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    CALLBACKS[tecla] = callback

    # observador já iniciado
    if len(CALLBACKS) > 1: return

    # iniciar observador
    def on_press (t: Key | str | Any) -> None:
        tecla = t.name if isinstance(t, Key) else str(t).strip("'")
        callback = CALLBACKS.get(tecla, lambda: None)
        callback()

    observador = Listener(on_press)
    observador.start()
    register(observador.stop)

__all__ = [
    "apertar_tecla",
    "atalho_teclado",
    "observar_tecla",
    "digitar_teclado"
]