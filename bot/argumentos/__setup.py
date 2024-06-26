# std
from sys import argv
# interno
import bot

argumentos = argv[1:] # primeiro argumento é sempre o nome do arquivo iniciado
posicionais: list[str] = []
nomeados: dict[str, str | None] = {}

def inicializar_argumentos () -> bool:
    """Inicializar os argumentos posicionais e nomeados
    - Retorna indicação se há algum argumento"""
    # posicionais
    while argumentos and not argumentos[0].startswith("--"):
        posicionais.append(argumentos.pop(0))

    # nomeados
    for index in range(0, len(argumentos) - 1):
        atual, proximo = argumentos[index], argumentos[index + 1]
        if not atual.startswith("--"): continue
        nomeados[atual.lstrip("-").lower()] = proximo if not proximo.startswith("-") else None

    return bool(posicionais or nomeados)

def posicional_existe (index: int) -> bool:
    """Checar se o argumento posicional existe"""
    try: return posicionais[index] != None
    except IndexError: return False

def nomeado_existe (nome: str) -> bool:
    """Checar se o argumento posicional existe"""
    return nome.strip().lower() in nomeados

def posicional_ou[T: bot.tipagem.primitivo] (index: int, default: T = "") -> T:
    """Obter o valor do argumento no `index` ou `default`
    - Transforma o tipo do argumento para o mesmo tipo do `default` informado"""
    return default if not posicional_existe(index) else \
        bot.util.transformar_tipo(posicionais[index], type(default))

def nomeado_ou[T: bot.tipagem.primitivo] (nome: str, default: T = "") -> T:
    """Obter o valor do argumento `nome` ou `default` caso não exista
    - Transforma o tipo do argumento para o mesmo tipo do `default` informado"""
    nome = nome.lower()
    return default if not nomeado_existe(nome) else \
        bot.util.transformar_tipo(nomeados[nome], type(default))

# inicializar no primeiro `import` do pacote
if inicializar_argumentos():
    mensagem = f"Argumento(s) de inicialização encontrado(s)\n\tPosicionais: {posicionais}\n\tNomeados: {nomeados}"
    bot.logger.informar(mensagem)

__all__ = [
    "nomeado_ou",
    "posicional_ou",
    "nomeado_existe",
    "posicional_existe"
]
