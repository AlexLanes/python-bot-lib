# std
import typing, configparser
# interno
from .. import util, estruturas, tipagem

INICIALIZADO = False
DIRETORIO_EXECUCAO = estruturas.Caminho.diretorio_execucao()
CONFIG = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())

def inicializar () -> None:
    """Inicializar o configfile"""
    assert DIRETORIO_EXECUCAO.diretorio()
    for caminho in DIRETORIO_EXECUCAO:
        if not caminho.arquivo() or not caminho.nome.endswith(".ini"): continue
        CONFIG.read(caminho.string, encoding="utf-8")

    global INICIALIZADO
    INICIALIZADO = True

def obter_secoes () -> list[str]:
    """Obter as seções do configfile"""
    if not INICIALIZADO: inicializar()
    return CONFIG.sections()

def opcoes_secao (secao: str) -> list[str]:
    """Obter as opções de uma `seção` do configfile"""
    if not INICIALIZADO: inicializar()
    return CONFIG.options(secao)

def possui_secao (secao: str) -> bool:
    """Indicador se uma `seção` está presente no configfile"""
    if not INICIALIZADO: inicializar()
    return CONFIG.has_section(secao)

def possui_opcao (secao: str, opcao: str) -> bool:
    """Indicador se uma `seção` possui a `opção` no configfile"""
    if not INICIALIZADO: inicializar()
    return CONFIG.has_option(secao, opcao)

def possui_opcoes (secao: str, opcoes: typing.Iterable[str]) -> bool:
    """Versão do `possui_opção` que aceita uma lista de `opções`"""
    return all(
        possui_opcao(secao, opcao)
        for opcao in opcoes
    )

def obter_opcao_ou[T: tipagem.primitivo] (secao: str, opcao: str, default: T = "") -> T:
    """Obter `opcao` de uma `secao` do configfile ou `default` caso não exista
    - Transforma o tipo da variável para o mesmo tipo do `default` informado"""
    return util.transformar_tipo(CONFIG.get(secao, opcao), type(default)) \
        if possui_secao(secao) and possui_opcao(secao, opcao) else default

def obter_opcoes (secao: str, opcoes: typing.Iterable[str]) -> tuple[str, ...]:
    """Obter `opções` de uma `seção` do configfile
    - Versão do `obter_opção` que aceita uma lista de `opções`
    - `AssertionError` caso a `seção` ou alguma `opção` não exista
    - `tuple` de retorno terá os valores na mesma ordem que as `opções`"""
    assert possui_secao(secao), f"Seção do configfile '{secao}' não foi configurada"
    assert possui_opcoes(secao, opcoes), f"Variáveis do configfile {str(opcoes)} não foram configuradas para a seção '{secao}'"
    return tuple(
        CONFIG.get(secao, opcao)
        for opcao in opcoes
    )

__all__ = [
    "opcoes_secao",
    "obter_secoes",
    "possui_opcao",
    "possui_secao",
    "obter_opcoes",
    "possui_opcoes",
    "obter_opcao_ou"
]
