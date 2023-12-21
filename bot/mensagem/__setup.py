# interno
from bot.tipagem import char
# externo
import pymsgbox


pymsgbox.CANCEL_TEXT = "Cancelar"


def alertar (texto: str, timeout=10000) -> None:
    """Mostrar caixa de mensagem de alerta informando o `texto`
    - `timeout` tempo em milissegundos para a caixa desaparecer caso não seja terminado"""
    pymsgbox.alert(texto, "Alerta", timeout=timeout)


def confirmar (texto: str, botaoConfirmar="Confirmar", botaoCancelar="Cancelar", timeout=10000) -> bool:
    """Mostrar caixa de mensagem de alerta informando o `texto`
    - `True` caso tenha sido clicado no `botaoConfirmar`
    - `timeout` tempo em milissegundos para a caixa desaparecer caso não seja terminado"""
    botao = pymsgbox.confirm(texto, "Confirmar", buttons=(botaoConfirmar, botaoCancelar), timeout=timeout)
    return botao == botaoConfirmar


def digitar (texto: str, mascara: char = None, timeout=10000) -> str | None:
    """Mostrar caixa de mensagem para ser digitado um valor
    - Retorna o texto digitado ou `None` caso timeout ou Cancelar
    - `mascara` char caso queira mascarar o que está sendo digitado
    - `timeout` tempo em milissegundos para a caixa desaparecer caso não seja terminado"""
    mensagem = pymsgbox.prompt(texto, "Digitar", timeout=timeout) if mascara == None else\
               pymsgbox.password(texto, "Digitar", mask=mascara[0], timeout=timeout)
    return mensagem if mensagem not in (None, "Timeout") else None


__all__ = [
    "alertar",
    "digitar",
    "confirmar"
]
