# std
from configparser import ConfigParser
# interno
import bot


config = ConfigParser()
arquivos = bot.windows.diretorio_execucao().arquivos
if nomes := [bot.windows.path.basename(caminho) for caminho in arquivos if caminho.endswith(".ini")]:
    [config.read(nome) for nome in nomes]


get = config.get
options = config.options
sections = config.sections
has_option = config.has_option
has_section = config.has_section


def has_options (secao: str, opcoes: list[str]) -> bool:
    """Versão do `has_option` que aceita uma lista de `opcoes`"""
    return all(config.has_option(secao, opcao) for opcao in opcoes)


def obter_opcoes (secao: str, opcoes: list[str]) -> tuple:
    """Obter `opções` de uma `seção` do configfile
    - Versão do `get` que aceita uma lista de `opcoes`
    - `AssertionError` caso a `secao` ou alguma `opcao` não exista
    - `tuple` de retorno terá os valores na mesma ordem que as `opcoes`"""
    assert has_section(secao), f"Seção do configfile '{ secao }' não foi configurada"
    assert has_options(secao, opcoes), f"Variáveis do configfile { str(opcoes) } não foram configuradas para a seção '{ secao }'"
    return tuple(get(secao, opcao) for opcao in opcoes)


__all__ = [
    "get",
    "options",
    "sections",
    "has_option",
    "has_options",
    "has_section",
    "obter_opcoes"
]
