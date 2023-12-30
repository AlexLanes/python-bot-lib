# std
from configparser import ConfigParser
# interno
from bot.windows import diretorio_execucao, path


config = ConfigParser()
for arquivo in diretorio_execucao().arquivos:
    if not arquivo.endswith(".ini"): continue
    config.read(path.basename(arquivo), encoding="utf-8")


obter_opcao = config.get
opcoes_secao = config.options
obter_secoes = config.sections
possui_opcao = config.has_option
possui_secao = config.has_section


def possui_opcoes (secao: str, opcoes: list[str]) -> bool:
    """Versão do `has_option` que aceita uma lista de `opcoes`"""
    return all(config.has_option(secao, opcao) for opcao in opcoes)


def obter_opcoes (secao: str, opcoes: list[str]) -> tuple[str, ...]:
    """Obter `opções` de uma `seção` do configfile
    - Versão do `get` que aceita uma lista de `opcoes`
    - `AssertionError` caso a `secao` ou alguma `opcao` não exista
    - `tuple` de retorno terá os valores na mesma ordem que as `opcoes`"""
    assert possui_secao(secao), f"Seção do configfile '{ secao }' não foi configurada"
    assert possui_opcoes(secao, opcoes), f"Variáveis do configfile { str(opcoes) } não foram configuradas para a seção '{ secao }'"
    return tuple(str(obter_opcao(secao, opcao)) for opcao in opcoes)


__all__ = [
    "obter_opcao",
    "opcoes_secao",
    "obter_secoes",
    "possui_opcao",
    "possui_secao",
    "obter_opcoes",
    "possui_opcoes"
]
