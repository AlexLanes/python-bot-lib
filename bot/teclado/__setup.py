# std
from time import sleep
from atexit import register
from typing import Callable
# interno
import bot
# externo
import pyperclip
from pynput.keyboard import Controller, Key, Listener


teclado = Controller()
callbacks_observador: dict[str, Callable[[], None]] = {}


def apertar_tecla (tecla: bot.tipagem.BOTOES_TECLADO, quantidade=1, delay=0.5) -> None:
    """Apertar e soltar uma tecla `qtd` vezes
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    # obter tecla no Enum(Key) se existir, se não char
    tecla: Key | str = Key[tecla] if any(tecla == k.name for k in Key) else tecla[0]
    for _ in range(max(quantidade, 1)): 
        teclado.tap(tecla)
        sleep(delay)


def atalho_teclado (teclas: list[bot.tipagem.BOTOES_TECLADO], delay=0.5) -> None:
    """Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    # obter teclas do Enum(Key) se existir, se não char
    teclas = [Key[tecla] if any(tecla == k.name for k in Key) else tecla[0] for tecla in teclas]
    for tecla in teclas: teclado.press(tecla) # pressionar teclas
    for tecla in reversed(teclas): teclado.release(tecla) # soltar teclas
    sleep(delay)


def digitar_teclado (texto: str, delay=0.02) -> None:
    """Digitar o texto pressionando cada tecla do texto e soltando em seguida"""
    for char in texto:
        teclado.type(char)
        sleep(delay)


def copiar_texto (texto: str) -> None:
    """Substituir o texto copiado da área de transferência pelo `texto`"""
    pyperclip.copy(texto)


def colar_texto_copiado () -> None:
    """Realizar ação `CTRL + V` com o texto copiado da área de transferência"""
    atalho_teclado(["ctrl", "v"])


def obter_texto_copiado (usoUnico=False) -> str:
    """Obter o texto copiado da área de transferência
    - `usoUnico` determina se o texto será apagado após ser obtido"""
    texto = pyperclip.paste()
    if usoUnico: copiar_texto("")
    return texto


def observar_tecla (tecla: bot.tipagem.BOTOES_TECLADO, callback: Callable[[], None]) -> None:
    """Observar quando a `tecla` é apertada e chamar o `callback`
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    callbacks_observador[tecla] = callback

    # observador já iniciado
    if len(callbacks_observador) > 1: return

    # iniciar observador
    def on_press (tecla: Key | str) -> None:
        tecla: str = tecla.name if isinstance(tecla, Key) else str(tecla).strip("'")
        callback = callbacks_observador.get(tecla, lambda: None)
        callback()

    observador = Listener(on_press)
    observador.start()
    register(observador.stop)


__all__ = [
    "copiar_texto",
    "apertar_tecla",
    "atalho_teclado",
    "observar_tecla",
    "digitar_teclado",
    "obter_texto_copiado",
    "colar_texto_copiado"
]
