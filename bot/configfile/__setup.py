# std
from typing import Iterable
from configparser import ConfigParser, ExtendedInterpolation
# interno
from bot.tipagem import primitivo
from bot.util import transformar_tipo
from bot.windows import diretorio_execucao, extrair_nome_base


config = ConfigParser(interpolation=ExtendedInterpolation())
for arquivo in diretorio_execucao().arquivos:
    if not arquivo.endswith(".ini"): continue
    config.read(extrair_nome_base(arquivo), encoding="utf-8")


opcoes_secao = config.options
obter_secoes = config.sections
possui_opcao = config.has_option
possui_secao = config.has_section


def possui_opcoes (secao: str, opcoes: Iterable[str]) -> bool:
    """Versão do `possui_opcao` que aceita uma lista de `opcoes`"""
    return all(config.has_option(secao, opcao) 
               for opcao in opcoes)


def obter_opcao_ou[T: primitivo] (secao: str, opcao: str, default: T = "") -> T:
    """Obter `opcao` de uma `secao` do configfile ou `default` caso não exista
    - Função genérica"""
    return transformar_tipo(config.get(secao, opcao), type(default)) \
        if possui_secao(secao) and possui_opcao(secao, opcao) else default


def obter_opcoes (secao: str, opcoes: Iterable[str]) -> tuple[str, ...]:
    """Obter `opções` de uma `seção` do configfile
    - Versão do `obter_opcao` que aceita uma lista de `opcoes`
    - `AssertionError` caso a `secao` ou alguma `opcao` não exista
    - `tuple` de retorno terá os valores na mesma ordem que as `opcoes`"""
    assert possui_secao(secao), f"Seção do configfile '{secao}' não foi configurada"
    assert possui_opcoes(secao, opcoes), f"Variáveis do configfile {str(opcoes)} não foram configuradas para a seção '{secao}'"
    return tuple(obter_opcao_ou(secao, opcao) for opcao in opcoes)


__all__ = [
    "opcoes_secao",
    "obter_secoes",
    "possui_opcao",
    "possui_secao",
    "obter_opcoes",
    "possui_opcoes",
    "obter_opcao_ou"
]
