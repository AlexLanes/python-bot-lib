# std
from sys import argv
# interno
import bot


argumentos = argv[1:] # primeiro argumento é sempre o nome do arquivo iniciado
posicionais: list[str] = []
nomeados: dict[str, str] = {}


class ArgumentosError (Exception): pass


def inicializar_argumentos () -> None:
    """Inicializar os argumentos posicionais e nomeados"""
    # posicionais
    while argumentos and not argumentos[0].startswith("--"):
        posicionais.append(argumentos.pop(0))

    if len(argumentos) <= 1: return

    # nomeados
    index = -1
    while index < len(argumentos) - 2:
        index += 1
        argumento, proximo = argumentos[index], argumentos[index + 1]
        if not argumento.startswith("--") or proximo.startswith("--"): continue
        nomeados[argumento.lstrip("-")] = proximo


def obter_argumento_nomeado (nome: str, default="", obrigatorio=False) -> str:
    """Obter o valor do argumento `nome` ou `default`
    - `ArgumentosError` caso `obrigatorio` e não encontrado"""
    if nome not in nomeados and obrigatorio: 
        raise ArgumentosError(f"Argumento nomeado obrigatório '{ nome }' não encontrado")
    return nomeados.get(nome, default)


def obter_argumento_posicional (index: int, default="", obrigatorio=False) -> str:
    """Obter o valor do argumento no `index` ou `default`
    - `ArgumentosError` caso `obrigatorio` e não encontrado"""
    valido = posicionais and index < len(posicionais)
    if not valido and obrigatorio: 
        raise ArgumentosError(f"Argumento posicional obrigatório '{ index }' não encontrado")
    return posicionais[index] if valido else default


inicializar_argumentos()
bot.logger.informar(
    f"""Argumento(s) de inicialização encontrado(s)
        Posicionais: { posicionais }
        Nomeados: { nomeados }"""
) if posicionais or nomeados else None


__all__ = [
    "ArgumentosError",
    "obter_argumento_nomeado",
    "obter_argumento_posicional"
]
