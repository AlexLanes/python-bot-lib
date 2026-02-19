# std
import re, configparser, typing
# interno
import bot
from bot.sistema import Caminho
from bot.estruturas import DictNormalizado

class Interpolacao (configparser.ExtendedInterpolation):
    # Aceita interpolação ${...}
    # Não necessário escapar char `$`

    RE_INTERPOLACAO = re.compile(r"\$\{([^}]+)\}")

    def before_get (self, parser: configparser.ConfigParser, # type: ignore
                          section: str,
                          option: str,
                          value: str,
                          defaults: dict[str, str]) -> str:
        return self.interpolar(parser, section, value, set(), 0)

    def interpolar (self, parser: configparser.ConfigParser,
                          section: str,
                          value: str,
                          seen: set[tuple[str, str]],
                          depth: int) -> str:
        if depth > 10:
            raise configparser.InterpolationDepthError(
                option  = "",
                section = section,
                rawval  = value,
            )

        def replace (match: re.Match[str]) -> str:
            key: str = match.group(1)

            # suporte a ${section:option}
            if ":" in key: secao, opcao = key.split(":", 1)
            else: secao, opcao = section, key

            ref: tuple[str, str] = (secao, opcao)
            if ref in seen: raise ValueError(f"Loop detectado em {ref}")
            seen.add(ref)

            # checar existência da interpolação
            assert parser.has_option(secao, opcao),\
                f"Falha na interpolação no configfile. Seção '{secao}' ou Opção '{opcao}' inexistente"

            raw = parser.get(secao, opcao, raw=True)
            return self.interpolar(parser, secao, raw, seen, depth + 1)

        return self.RE_INTERPOLACAO.sub(replace, value)

class ConfigFile:
    """Classe para inicialização de variáveis a partir de arquivo de configuração `.ini`  

    #### Inicializado automaticamente na primeira consulta

    - Para concatenação de valores, utilizar a sintaxe `${opção}` `${seção:opção}`
    - `#` ou `;` comenta a linha se tiver no começo
    - Arquivos terminados em `.ini` devem estar presente em `DIRETORIO_EXECUCAO`
    ```"""

    INICIALIZADO: bool = False
    DIRETORIO_EXECUCAO = Caminho.diretorio_execucao()
    DADOS = DictNormalizado[DictNormalizado[str]]()
    """`{ secao: { opcao: valor } }`"""

    def __repr__ (self) -> str:
        return f"<bot.ConfigFile com '{len(self.DADOS)}' seções>"

    @property
    def parser (self) -> configparser.ConfigParser:
        return configparser.ConfigParser(
            interpolation = Interpolacao()
        )

    def inicializar_configfile (self) -> typing.Self:
        """Inicializar o configfile"""
        if self.INICIALIZADO: return self
        self.INICIALIZADO = True

        parser = self.parser
        for caminho in self.DIRETORIO_EXECUCAO.criar_diretorios():
            if not caminho.arquivo() or not caminho.nome.endswith(".ini"): continue
            parser.read(caminho.string, encoding="utf-8")

        # lower seções e opções
        for secao in parser:
            if secao.lower() == "default": continue
            self.DADOS[secao] = DictNormalizado({
                opcao: parser[secao][opcao]
                for opcao in parser[secao]
            })

        return self

    def obter_secoes (self) -> list[str]:
        """Obter as seções do configfile"""
        return list(self.inicializar_configfile().DADOS)

    def opcoes_secao (self, secao: str) -> list[str]:
        """Obter as opções de uma `seção` do configfile"""
        return list(self.inicializar_configfile().DADOS[secao])

    def possui_secao (self, secao: str) -> bool:
        """Indicador se uma `seção` está presente no configfile"""
        return secao in self.inicializar_configfile().DADOS

    def possui_opcao (self, secao: str, opcao: str) -> bool:
        """Indicador se uma `seção` possui a `opção` no configfile"""
        return opcao in self.inicializar_configfile().DADOS[secao]

    def possui_opcoes (self, secao: str, *opcoes: str) -> bool:
        """Versão do `possui_opcao` que aceita múltiplas `opções`"""
        self.inicializar_configfile()
        return all(
            self.possui_opcao(secao, opcao)
            for opcao in opcoes
        )

    def obter_opcao_ou[T: bot.tipagem.primitivo] (self, secao: str, opcao: str, default: T = "") -> T:
        """Obter `opcao` de uma `secao` do configfile ou `default` caso não exista
        - Transforma o tipo da variável para o mesmo tipo do `default` informado"""
        self.inicializar_configfile()
        return bot.util.transformar_tipo(self.DADOS[secao][opcao], type(default)) \
            if self.possui_secao(secao) and self.possui_opcao(secao, opcao) else default

    def obter_opcoes_obrigatorias (self, secao: str, *opcoes: str) -> tuple[str, ...]:
        """Obter múltiplas `opções` de uma `seção`
        - `AssertionError` caso a `seção` ou alguma `opção` não exista
        - `tuple` de retorno terá os valores na mesma ordem que as `opções`"""
        assert self.possui_secao(secao), f"Seção do configfile '{secao}' não foi configurada"
        assert self.possui_opcoes(secao, *opcoes), f"Variáveis do configfile {str(opcoes)} não foram configuradas para a seção '{secao}'"
        return tuple(
            self.DADOS[secao][opcao]
            for opcao in opcoes
        )

configfile = ConfigFile()
"""Classe para inicialização de variáveis a partir de arquivo de configuração `.ini`  

#### Inicializado automaticamente na primeira consulta

- Para concatenação de valores, utilizar a sintaxe `${opção}` `${seção:opção}`
- `#` ou `;` comenta a linha se tiver no começo
- Arquivos terminados em `.ini` devem estar presente em `DIRETORIO_EXECUCAO`
```"""

__all__ = ["configfile"]