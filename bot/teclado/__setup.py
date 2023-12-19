# interno
import bot
# externo
import pyperclip
from pynput.keyboard import Controller, Key


teclado = Controller()


def apertar_tecla (tecla: bot.tipagem.BOTOES_TECLADO, qtd=1) -> None:
    """Apertar e soltar uma tecla `qtd` vezes
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char` a, 1, Ç, @"""
    # obter tecla no Enum(Key) se existir, se não char
    tecla: Key | str = Key[tecla] if any(tecla == k.name for k in Key) else tecla[0]
    for _ in range(max(qtd, 1)): teclado.tap(tecla)


def atalho_teclado (teclas: list[bot.tipagem.BOTOES_TECLADO]) -> None:
    """Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char` a, 1, Ç, @"""
    # obter teclas do Enum(Key) se existir, se não char
    teclas = [Key[tecla] if any(tecla == k.name for k in Key) else tecla[0] for tecla in teclas]
    for tecla in teclas: teclado.press(tecla) # pressionar teclas
    for tecla in reversed(teclas): teclado.release(tecla) # soltar teclar


def digitar_teclado (texto: str) -> None:
    """Digitar o texto pressionando cada tecla do texto e soltando em seguida"""
    texto = str(texto)
    teclado.type(texto)


def copiar_texto (texto: str) -> None:
    """Substituir o texto copiado da área de transferência pelo `texto`"""
    pyperclip.copy(texto)


def colar_texto () -> None:
    """Realizar ação `CTRL + V` com o texto copiado da área de transferência"""
    atalho_teclado(["ctrl", "v"])


def texto_copiado (usoUnico=False) -> str:
    """Obter o texto copiado da área de transferência
    - `usoUnico` determina se o texto será apagado após ser obtido"""
    texto = pyperclip.paste()
    if usoUnico: copiar_texto("")
    return texto


__all__ = [
    "colar_texto",
    "copiar_texto",
    "texto_copiado",
    "apertar_tecla",
    "atalho_teclado",
    "digitar_teclado"
]
