# std
import os, typing
from configparser import ConfigParser, ExtendedInterpolation
# interno
from .. import util, windows, estruturas, tipagem

CAMINHO_PACOTE = windows.nome_diretorio(__file__).removesuffix(r"\argumentos")
CAMINHO_IMPORTADOR = windows.nome_diretorio(estruturas.InfoStack.caminhos()[-1])
DIRETORIO_EXECUCAO = CAMINHO_IMPORTADOR if CAMINHO_IMPORTADOR != CAMINHO_PACOTE else os.getcwd()

# inicializar no primeiro `import` do pacote
CONFIG = ConfigParser(interpolation=ExtendedInterpolation())
for arquivo in windows.listar_diretorio(DIRETORIO_EXECUCAO).arquivos:
    if not arquivo.endswith(".ini"): continue
    CONFIG.read(arquivo, encoding="utf-8")

opcoes_secao = CONFIG.options
obter_secoes = CONFIG.sections
possui_opcao = CONFIG.has_option
possui_secao = CONFIG.has_section

def possui_opcoes (secao: str, opcoes: typing.Iterable[str]) -> bool:
    """Versão do `possui_opção` que aceita uma lista de `opções`"""
    return all(
        CONFIG.has_option(secao, opcao)
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
