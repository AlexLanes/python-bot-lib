# std
from typing import Iterable
from configparser import ConfigParser, ExtendedInterpolation
# interno
from bot.tipagem import primitivo
from bot.util import transformar_tipo
from bot.windows import diretorio_execucao, nome_base

# inicializar no primeiro `import` do pacote
CONFIG = ConfigParser(interpolation=ExtendedInterpolation())
for arquivo in diretorio_execucao().arquivos:
    if not arquivo.endswith(".ini"): continue
    CONFIG.read(nome_base(arquivo), encoding="utf-8")

opcoes_secao = CONFIG.options
obter_secoes = CONFIG.sections
possui_opcao = CONFIG.has_option
possui_secao = CONFIG.has_section

def possui_opcoes (secao: str, opcoes: Iterable[str]) -> bool:
    """Versão do `possui_opção` que aceita uma lista de `opções`"""
    return all(
        CONFIG.has_option(secao, opcao)
        for opcao in opcoes
    )

def obter_opcao_ou[T: primitivo] (secao: str, opcao: str, default: T = "") -> T:
    """Obter `opcao` de uma `secao` do configfile ou `default` caso não exista
    - Transforma o tipo da variável para o mesmo tipo do `default` informado"""
    return transformar_tipo(CONFIG.get(secao, opcao), type(default)) \
        if possui_secao(secao) and possui_opcao(secao, opcao) else default

def obter_opcoes (secao: str, opcoes: Iterable[str]) -> tuple[str, ...]:
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
