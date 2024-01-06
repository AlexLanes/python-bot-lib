# interno
import bot
# externo
import pyperclip
from pynput.keyboard import Controller, Key


teclado = Controller()


def apertar_tecla (tecla: bot.tipagem.BOTOES_TECLADO, quantidade=1) -> None:
    """Apertar e soltar uma tecla `qtd` vezes
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    # obter tecla no Enum(Key) se existir, se não char
    tecla: Key | str = Key[tecla] if any(tecla == k.name for k in Key) else tecla[0]
    for _ in range(max(quantidade, 1)): teclado.tap(tecla)


def atalho_teclado (teclas: list[bot.tipagem.BOTOES_TECLADO]) -> None:
    """Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa
    - `tecla` pode ser do `BOTOES_TECLADO` ou um `char`"""
    # obter teclas do Enum(Key) se existir, se não char
    teclas = [Key[tecla] if any(tecla == k.name for k in Key) else tecla[0] for tecla in teclas]
    for tecla in teclas: teclado.press(tecla) # pressionar teclas
    for tecla in reversed(teclas): teclado.release(tecla) # soltar teclas


def digitar_teclado (texto: str) -> None:
    """Digitar o texto pressionando cada tecla do texto e soltando em seguida"""
    teclado.type(str(texto))


def copiar_texto (texto: str) -> None:
    """Substituir o texto copiado da área de transferência pelo `texto`"""
    pyperclip.copy(str(texto))


def colar_texto_copiado () -> None:
    """Realizar ação `CTRL + V` com o texto copiado da área de transferência"""
    atalho_teclado(["ctrl", "v"])


def obter_texto_copiado (usoUnico=False) -> str:
    """Obter o texto copiado da área de transferência
    - `usoUnico` determina se o texto será apagado após ser obtido"""
    texto = pyperclip.paste()
    if usoUnico: copiar_texto("")
    return texto


__all__ = [
    "copiar_texto",
    "apertar_tecla",
    "atalho_teclado",
    "digitar_teclado",
    "obter_texto_copiado",
    "colar_texto_copiado"
]
