# std
import sys, itertools
# interno
from .. import util, tipagem

ARGUMENTOS = sys.argv[1:] # primeiro argumento é sempre o nome do arquivo iniciado
POSICIONAIS: list[str] = []
NOMEADOS: dict[str, str] = {}

# ------------------------------------------ #
# Inicializar no primeiro `import` do pacote #
# ------------------------------------------ #
# posicionais
while ARGUMENTOS and not ARGUMENTOS[0].startswith("--"):
    POSICIONAIS.append(ARGUMENTOS.pop(0))
# nomeados
for atual, proximo in itertools.pairwise(itertools.chain(ARGUMENTOS, [""])):
    if not atual.startswith("--"): continue
    NOMEADOS[atual.lstrip("-").lower()] = proximo if not proximo.startswith("--") else ""

def posicional_existe (index: int) -> bool:
    """Checar se o argumento posicional existe"""
    try: return POSICIONAIS[index] != None
    except IndexError: return False

def nomeado_existe (nome: str) -> bool:
    """Checar se o argumento posicional existe"""
    return nome.strip().lower() in NOMEADOS

def posicional_ou[T: tipagem.primitivo] (index: int, default: T = "") -> T:
    """Obter o valor do argumento no `index` ou `default`
    - Transforma o tipo do argumento para o mesmo tipo do `default` informado"""
    return default if not posicional_existe(index) else \
        util.transformar_tipo(POSICIONAIS[index], type(default))

def nomeado_ou[T: tipagem.primitivo] (nome: str, default: T = "") -> T:
    """Obter o valor do argumento `nome` ou `default` caso não exista
    - Transforma o tipo do argumento para o mesmo tipo do `default` informado"""
    nome = nome.lower()
    return default if not nomeado_existe(nome) else \
        util.transformar_tipo(NOMEADOS[nome], type(default))

__all__ = [
    "nomeado_ou",
    "posicional_ou",
    "nomeado_existe",
    "posicional_existe"
]
