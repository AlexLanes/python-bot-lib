# std
import configparser
# interno
from .. import util, sistema, tipagem, estruturas

INICIALIZADO = False
DIRETORIO_EXECUCAO = sistema.Caminho.diretorio_execucao()
DADOS = estruturas.LowerDict[estruturas.LowerDict[str]]()
"""`{ secao: { opcao: valor } }`"""

def inicializar_configfile (diretorio = DIRETORIO_EXECUCAO) -> None:
    """Inicializar o configfile"""
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    for caminho in diretorio.criar_diretorios():
        if not caminho.arquivo() or not caminho.nome.endswith(".ini"): continue
        config.read(caminho.string, encoding="utf-8")

    global INICIALIZADO
    INICIALIZADO = True

    # lower seções e opções
    for secao in config:    
        if secao.lower() == "default": continue
        DADOS[secao] = estruturas.LowerDict({
            opcao: config[secao][opcao]
            for opcao in config[secao]
        })

def obter_secoes () -> list[str]:
    """Obter as seções do configfile"""
    if not INICIALIZADO: inicializar_configfile()
    return list(DADOS)

def opcoes_secao (secao: str) -> list[str]:
    """Obter as opções de uma `seção` do configfile"""
    if not INICIALIZADO: inicializar_configfile()
    return list(DADOS[secao])

def possui_secao (secao: str) -> bool:
    """Indicador se uma `seção` está presente no configfile"""
    if not INICIALIZADO: inicializar_configfile()
    return secao in DADOS

def possui_opcao (secao: str, opcao: str) -> bool:
    """Indicador se uma `seção` possui a `opção` no configfile"""
    if not INICIALIZADO: inicializar_configfile()
    return opcao in DADOS[secao]

def possui_opcoes (secao: str, *opcoes: str) -> bool:
    """Versão do `possui_opcao` que aceita múltiplas `opções`"""
    return all(
        possui_opcao(secao, opcao)
        for opcao in opcoes
    )

def obter_opcao_ou[T: tipagem.primitivo] (secao: str, opcao: str, default: T = "") -> T:
    """Obter `opcao` de uma `secao` do configfile ou `default` caso não exista
    - Transforma o tipo da variável para o mesmo tipo do `default` informado"""
    return util.transformar_tipo(DADOS[secao][opcao], type(default)) \
        if possui_secao(secao) and possui_opcao(secao, opcao) else default

def obter_opcoes_obrigatorias (secao: str, *opcoes: str) -> tuple[str, ...]:
    """Obter múltiplas `opções` de uma `seção`
    - `AssertionError` caso a `seção` ou alguma `opção` não exista
    - `tuple` de retorno terá os valores na mesma ordem que as `opções`"""
    assert possui_secao(secao), f"Seção do configfile '{secao}' não foi configurada"
    assert possui_opcoes(secao, *opcoes), f"Variáveis do configfile {str(opcoes)} não foram configuradas para a seção '{secao}'"
    return tuple(
        DADOS[secao][opcao]
        for opcao in opcoes
    )

__all__ = [
    "opcoes_secao",
    "obter_secoes",
    "possui_opcao",
    "possui_secao",
    "possui_opcoes",
    "obter_opcao_ou",
    "obter_opcoes_obrigatorias",
]