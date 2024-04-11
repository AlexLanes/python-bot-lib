# std
from sys import argv
# interno
from bot import logger
from bot.tipagem import primitivo


argumentos = argv[1:] # primeiro argumento é sempre o nome do arquivo iniciado
posicionais: list[str] = []
nomeados: dict[str, str | None] = {}


def inicializar_argumentos () -> None:
    """Inicializar os argumentos posicionais e nomeados"""
    # posicionais
    while argumentos and not argumentos[0].startswith("--"):
        posicionais.append(argumentos.pop(0))

    # nomeados
    for index in range(0, len(argumentos) - 1):
        atual, proximo = argumentos[index], argumentos[index + 1]
        if not atual.startswith("--"): continue
        nomeados[atual.lstrip("-")] = proximo if not proximo.startswith("-") else None


def transformar_tipo[T: primitivo] (valor: str, tipo: type[T]) -> T:
    """Fazer a transformação do `valor` para `type(tipo)`
    - Helper"""
    match str(tipo):
        case "<class 'str'>": return valor
        case "<class 'int'>" | "<class 'float'>": return tipo(valor)
        case "<class 'bool'>": return valor.lower().strip() == "true"
        case _: return None


def nomeado_existe (nome: str) -> bool:
    """Checar se o argumento posicional existe"""
    return nome in nomeados


def nomeado_ou[T: primitivo] (nome: str, default: T = "") -> T:
    """Obter o valor do argumento `nome` ou `default`
    - Função `genérica`"""
    return transformar_tipo(nomeados[nome], type(default)) \
        if nomeado_existe(nome) else default


def posicional_existe (index: int) -> bool:
    """Checar se o argumento posicional existe"""
    return posicionais and index < len(posicionais)


def posicional_ou[T: primitivo] (index: int, default: T = "") -> T:
    """Obter o valor do argumento no `index` ou `default`
    - Função `genérica`"""
    return transformar_tipo(posicionais[index], type(default)) \
        if posicional_existe(index) else default


inicializar_argumentos()
logger.informar(
    f"""Argumento(s) de inicialização encontrado(s)
        Posicionais: {posicionais}
        Nomeados: {nomeados}"""
) if posicionais or nomeados else None


__all__ = [
    "nomeado_ou",
    "posicional_ou",
    "nomeado_existe",
    "posicional_existe"
]
