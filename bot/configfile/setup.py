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

class SecaoConfigFile:
    def __init__ (self, nome: str, dados: DictNormalizado[str]) -> None:
        self.__nome = nome
        self.__dados = dados

    def __repr__ (self) -> str:
        return f"<SeçãoConfigFile Nome={self.__nome!r} Opções={self.opcoes()!r}>"

    def __len__ (self) -> int:
        return len(self.__dados)

    def __getattr__ (self, nome: str) -> str:
        if (valor := self.__dados.get(nome, None)) is not None:
            return valor
        raise AttributeError(f"Opção '{nome}' não encontrada em {self}")

    def __contains__ (self, item: object) -> bool:
        if not isinstance(item, str):
            return NotImplemented
        return item in self.__dados

    def opcoes (self) -> list[str]:
        """Obter as Opções da Seção"""
        return list(self.__dados)

    def as_dict (self) -> dict[str, str]:
        return dict(self.__dados)

    def obter_ou[T: bot.tipagem.primitivo] (self, opcao: str, default: T = "") -> T:
        """Obter a `opção` da Seção ou `default` caso não exista
        - Transforma o tipo para o mesmo do `default` informado"""
        if (valor := self.__dados.get(opcao, None)) is not None:
            return bot.util.transformar_tipo(valor, type(default))
        return default

    def obter (self, *opcao: str) -> tuple[str, ...]:
        """Obter múltiplas Opções da Seção
        - Retorno dos valores na mesma ordem"""
        assert opcao, f"Informar ao menos 1 opção {self}"
        return tuple(
            getattr(self, nome)
            for nome in opcao
        )

class ConfigFile:
    """Classe para inicialização de variáveis a partir de arquivo de configuração `.ini`
    - Para concatenação de valores, utilizar a sintaxe `${opção}` `${seção:opção}`
    - `#` ou `;` comenta a linha se tiver no começo
    - Arquivos terminados em `.ini` devem estar presente em `DIRETORIO_EXECUCAO`

    ### Exemplo
    ```
    [LOGIN]
    usuario = rpa
    senha = 123

    [email]
    usuario = ${LOGIN:usuario}@gmail.com
    ativado = True
    ```
    ### Utilização
    ```python
    import bot

    print("Secões", bot.config.secoes())
    assert "minha_secao" in bot.config

    secao = bot.config.minha_secao
    print(secao)
    print("Opções Seção", secao.opcoes())

    if "usuario" in secao:
        print(secao.usuario)
    print(secao.obter_ou("usuario", default=""))
    a, b, c = secao.obter("a", "b", "c")
    ```
    """

    DIRETORIO_EXECUCAO = Caminho.DiretorioExecucao()
    __dados: DictNormalizado[SecaoConfigFile]
    """`{ secao: SecaoConfigFile }`"""

    def __repr__ (self) -> str:
        return f"<bot.ConfigFile Seções={getattr(self, "__secoes")!r}>"

    def inicializar (self, caminho: Caminho | None = None) -> typing.Self:
        """Inicializar o `ConfigFile`
        - `caminho=None` inicializar buscando todos os `.ini` no `DIRETORIO_EXECUCAO`"""
        parser = configparser.ConfigParser(
            interpolation = Interpolacao()
        )
        parser.optionxform = lambda optionstr: optionstr.lower().replace(".", "_")

        match caminho:
            case Caminho():
                parser.read(caminho.string, encoding="utf-8")
            case None:
                for caminho in self.DIRETORIO_EXECUCAO:
                    if not caminho.arquivo() or not caminho.nome.endswith(".ini"): continue
                    parser.read(caminho.string, encoding="utf-8")

        secoes = {
            nome.replace(".", "_"): secao
            for nome, secao in parser.items()
            if nome.lower() != "default"
        }

        setattr(self, "__secoes", list(secoes))
        self.__dados = DictNormalizado({
            nome: SecaoConfigFile(nome, DictNormalizado(secao))
            for nome, secao in secoes.items()
        })

        return self

    def __len__ (self) -> int:
        return len(self.__dados)

    def __getattr__ (self, nome: str) -> SecaoConfigFile:
        if (valor := self.__dados.get(nome, None)) is not None:
            return valor
        raise AttributeError(f"Seção '{nome}' não encontrada em {self}")

    def __contains__ (self, item: object) -> bool:
        if not isinstance(item, str):
            return NotImplemented
        return item.replace(".", "_") in self.__dados

    def secoes (self) -> list[str]:
        """Obter as Seções do `ConfigFile`"""
        return list(getattr(self, "__secoes"))

config = ConfigFile().inicializar()
"""Classe para inicialização de variáveis a partir de arquivo de configuração `.ini`  
- Para concatenação de valores, utilizar a sintaxe `${opção}` `${seção:opção}`
- `#` ou `;` comenta a linha se tiver no começo
- Arquivos terminados em `.ini` devem estar presente em `DIRETORIO_EXECUCAO`

### Exemplo
```
[LOGIN]
usuario = rpa
senha = 123

[email]
usuario = ${LOGIN:usuario}@gmail.com
ativado = True
```
### Utilização
```python
import bot

print("Secões", bot.config.secoes())
assert "minha_secao" in bot.config

secao = bot.config.minha_secao
print(secao)
print("Opções Seção", secao.opcoes())

if "usuario" in secao:
    print(secao.usuario)
print(secao.obter_ou("usuario", default=""))
a, b, c = secao.obter("a", "b", "c")
```
"""

__all__ = ["config"]