# interno
import bot
# externo
import pyperclip
from pynput.keyboard import Controller


teclado = Controller()


def apertar_tecla (tecla: bot.tipagem.BOTOES_TECLADO, qtd = 1, intervalo = 0.1) -> None:
    """Apertar e soltar uma tecla do teclado `qtd` vezes"""
    bot.pyautogui.press(tecla, qtd, intervalo)


def atalho_teclado (teclas: list[bot.tipagem.BOTOES_TECLADO], intervalo = 0.1) -> None:
    """Apertar as teclas sequencialmente a cada `intervalo` segundos e depois soltá-las em ordem reversa"""
    bot.pyautogui.hotkey(teclas, interval=intervalo)


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
