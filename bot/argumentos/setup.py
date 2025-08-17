# std
import sys, itertools
# interno
import bot

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

def posicionais () -> list[str]:
    """Obter os argumentos posicionais"""
    return POSICIONAIS.copy()

def nomeado_existe (nome: str) -> bool:
    """Checar se o argumento nomeado existe"""
    return nome.strip().lower() in NOMEADOS

def nomeado_ou[T: bot.tipagem.primitivo] (nome: str, default: T = "") -> T:
    """Obter o valor do argumento `nome` ou `default` caso não exista
    - Transforma o tipo do argumento para o mesmo tipo do `default` informado"""
    nome = nome.lower()
    return default if not nomeado_existe(nome) else \
        bot.util.transformar_tipo(NOMEADOS[nome], type(default))

__all__ = [
    "nomeado_ou",
    "posicionais",
    "nomeado_existe",
]