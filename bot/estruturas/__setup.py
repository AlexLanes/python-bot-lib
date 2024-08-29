# std
from __future__ import annotations
from inspect import stack
from dataclasses import dataclass
from functools import cached_property
from typing import Generator, Callable
from datetime import datetime as Datetime
from itertools import tee as duplicar_iterable
from os.path import getmtime as ultima_alteracao
# interno
from .. import tipagem, windows
# externo
from polars import DataFrame

@dataclass
class Coordenada:
    """Coordenada de uma região na tela"""

    x: int
    y: int
    largura: int
    altura: int

    def __iter__ (self) -> Generator[int, None, None]:
        """Utilizado com o `tuple(coordenada)` e `x, y, largura, altura = coordenada`"""
        yield self.x
        yield self.y
        yield self.largura
        yield self.altura

    def __len__ (self) -> int:
        return 4

    def __contains__ (self, other: Coordenada | tuple[int, int]) -> bool:
        """Testar se o ponto central da coordenada está dentro da outra
        - `coordenada in coordenada2`"""
        if not isinstance(other, Coordenada) and not isinstance(other, tuple):
            return False

        x, y = other.transformar() if isinstance(other, Coordenada) else other
        return x in range(self.x, self.x + self.largura + 1) \
           and y in range(self.y, self.y + self.altura + 1)

    def __hash__ (self) -> int:
        return hash(repr(self))

    def transformar (self, xOffset=0.5, yOffset=0.5) -> tuple[int, int]:
        """Transformar as cordenadas para a posição (X, Y) de acordo com a porcentagem `xOffset` e `yOffset`
        - (X, Y) central caso os offsets não tenham sido informados
        - `xOffset` esquerda, centro, direita = 0.0, 0.5, 1.0
        - `yOffset` topo, centro, baixo = 0.0, 0.5, 1.0"""
        # enforça o range entre 0.0 e 1.0
        xOffset, yOffset = max(0.0, min(1.0, xOffset)), max(0.0, min(1.0, yOffset))
        return (
            self.x + int(self.largura * xOffset),
            self.y + int(self.altura * yOffset)
        )

    @classmethod
    def from_box (cls, box: tuple[int, int, int, int]) -> Coordenada:
        """Criar coordenada a partir de uma box
        - `box`: `X esquerda-direita` + `Y esquerda-direita`
        - `@classmethod`"""
        x, y = int(box[0]), int(box[2])
        largura, altura = int(box[1] - x), int(box[3] - y)
        return cls(x, y, largura, altura)

@dataclass
class ResultadoSQL:
    """Classe utilizada no retorno de comando em banco de dados

    ```
    # representação "vazio", "com linhas afetadas" ou "com colunas e linhas"
    repr(resultado)
    resultado.linhas_afetadas != None # para comandos de manipulação
    resultado.colunas # para comandos de consulta

    # teste de sucesso, indica se teve linhas_afetadas ou linhas/colunas retornadas
    bool(resultado) | if resultado: ...

    # quantidade de linhas retornadas
    len(resultado)

    # iteração sobre as linhas `Generator`
    # as linhas são consumidas quando iteradas sobre
    linha: tuple[tipagem.tipoSQL, ...] = next(resultado.linhas)
    for linha in resultado.linhas:
    for linha in resultado:

    # fácil acesso a primeira linha
    resultado["nome_coluna"]
    ```"""

    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica para o comando sql"""
    colunas: tuple[str, ...]
    """Colunas das linhas retornadas (se houver)"""
    linhas: Generator[tuple[tipagem.tipoSQL, ...], None, None]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    def __iter__ (self) -> Generator[tuple[tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    @cached_property
    def __p (self) -> tuple[tipagem.tipoSQL, ...] | None:
        """Cache da primeira linha no resultado
        - `None` caso não possua"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        try: return next(linhas)
        except StopIteration: return None

    def __repr__ (self) -> str:
        "Representação da classe"
        tipo = f"com {self.linhas_afetadas} linha(s) afetada(s)" if self.linhas_afetadas \
            else f"com {len(self.colunas)} coluna(s) e {len(self)} linha(s)" if self.__p \
            else f"vazio"
        return f"<ResultadoSQL {tipo}>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return "vazio" not in repr(self)

    def __len__ (self) -> int:
        """Obter a quantidade de linhas no retornadas"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        return sum(1 for _ in linhas)

    def __getitem__ (self, campo: str) -> tipagem.tipoSQL:
        """Obter o `campo` da primeira linha"""
        return self.__p[self.colunas.index(campo)]

    @property
    def __dict__ (self) -> dict[str, int | None | list[dict]]:
        """Representação formato dicionário"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        return {
            "linhas_afetadas": self.linhas_afetadas,
            "resultados": [
                { 
                    coluna: valor
                    for coluna, valor in zip(self.colunas, linha)
                }
                for linha in linhas
            ]
        }

    def to_dataframe (self, transformar_string=False) -> DataFrame:
        """Salvar o resultado em um `polars.DataFrame`
        - `transformar_string` flag se os dados serão convertidos em `str`"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        to_string = lambda linha: tuple(
            str(valor) if valor != None else None
            for valor in linha
        )
        return DataFrame(
            map(to_string, linhas) if transformar_string else linhas,
            self.colunas,
            nan_to_null=True
        )

class Resultado [T]:
    """Classe `genérica` de utilização para retornar resultado de alguma chamada
    - `try-catch` utilizado para evitar erro

    ```
    # informar a função, os argumentos posicionais e os argumentos nomeados
    # a função será automaticamente chamada após
    resultado = Resultado(funcao, "nome", "idade", key=value)

    # representação "sucesso" ou "erro"
    repr(resultado)

    # checar sucesso na chamada
    bool(resultado) | if resultado: ...

    # obtendo valores
    valor, erro = resultado._()
    valor = resultado.valor() # erro caso a função tenha apresentado erro
    valor = resultado.valor_ou(default) # valor ou default caso a função tenha apresentado erro
    ```"""

    __valor: T | None
    __erro: Exception | None

    def __init__ (self, funcao: Callable[..., T], *args, **kwargs) -> None:
        """Realizar a chamada na `função` com os argumentos `args` e `kwargs`"""
        self.__valor = self.__erro = None
        try: self.__valor = funcao(*args, **kwargs)
        except Exception as erro: self.__erro = erro

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.__erro == None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Resultado[T] {"sucesso" if self else "erro"}>"

    def _ (self) -> tuple[T | None, Exception | None]:
        """Realizar unwrap do `valor, erro = resultado._()`"""
        return self.__valor, self.__erro

    def valor (self) -> T:
        """Obter o valor do resultado
        - `raise Exception` caso tenha apresentado erro"""
        if not self:
            self.__erro.add_note("Valor não presente no resultado")
            raise self.__erro
        return self.__valor

    def valor_ou (self, default: T) -> T:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        return self.__valor if self else default

@dataclass
class Diretorio:
    """Armazena os caminhos de pastas e arquivos presentes no diretório"""

    caminho: tipagem.caminho
    """Caminho absoluto do diretorio"""
    pastas: list[tipagem.caminho]
    """Lista contendo o caminho de cada pasta do diretório"""
    arquivos: list[tipagem.caminho]
    """Lista contendo o caminho de cada arquivo do diretório"""

    def __repr__ (self) -> str:
        return f"<Diretorio '{self.caminho}' com {len(self.pastas)} pasta(s) e {len(self.arquivos)} arquivos(s)>"

    def query_data_alteracao_arquivos (self,
                                       inicio=Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                       fim=Datetime.now()) -> list[tuple[tipagem.caminho, Datetime]]:
        """Consultar arquivos do diretório com base na data de alteração
        - Default: Hoje
        - Retorna uma lista `(caminho, data)` ordenado pelos mais antigos"""
        criar_data = lambda caminho: Datetime.fromtimestamp(ultima_alteracao(caminho))
        return sorted(
            (
                (caminho, data)
                for caminho in self.arquivos
                if inicio <= (data := criar_data(caminho)) <= fim
            ),
            key = lambda x: x[1]
        )

class InfoStack:
    """Informações do `Stack` de execução"""

    nome: str
    """Nome do arquivo"""
    funcao: str
    """Nome da função"""
    linha: int
    """Linha do item executado"""
    caminho: tipagem.caminho
    """Caminho do arquivo"""

    def __init__ (self, index=1) -> None:
        """Obter informações presente no stack dos callers
        - `Default` arquivo que chamou o `InfoStack()`"""
        frame = stack()[index]
        self.linha, self.funcao = frame.lineno, frame.function
        self.nome = windows.nome_base(frame.filename)
        self.caminho = windows.nome_diretorio(frame.filename)

    @staticmethod
    def caminhos () -> list[tipagem.caminho]:
        """Listar os caminhos dos callers no stack de execução
        - `[0] topo stack`
        - `[-1] começo stack`"""
        return [
            windows.caminho_absoluto(frame.filename)
            for frame in stack()
            if windows.afirmar_arquivo(frame.filename)
        ]

@dataclass
class Email:
    """Classe para armazenar informações extraídas de Email"""

    uid: int
    """id do e-mail"""
    remetente: tipagem.email
    """Remetente que enviou o e-mail"""
    destinatarios: list[tipagem.email]
    """Destinatários que receberam o e-mail"""
    assunto: str
    """Assunto do e-mail"""
    data: Datetime
    """Data de envio do e-mail"""
    texto: str | None
    """Conteúdo do e-mail como texto"""
    html: str | None
    """Conteúdo do e-mail como html"""
    anexos: list[tuple[str, str, bytes]]
    """Anexos do e-mail
    - `for nome, tipo, conteudo in email.anexos:`"""

class LowerDict [T]:
    """Classe usada para obter/criar/adicionar chaves de um `dict` como `lower-case`
    - Obter: `LowerDict["nome"]` KeyError caso não exista
    - Checar existência: `"nome" in LowerDict`
    - Adicionar/Atualizar: `LowerDict["nome"] = "valor"`
    - Tamanho: `len(LowerDict)` quantidade de chaves
    - Iteração: `for chave in LowerDict: ...`
    - Comparador bool: `bool(LowerDict)` ou `if LowerDict: ...` True se não for vazio
    - Comparador igualdade: `LowerDict1 == LowerDict2` True se as chaves, valores e tamanho forem iguais"""

    __d: dict[str, T]

    def __init__ (self, d: dict[str, T] | None = None) -> None:
        self.__d = {
            chave.lower().strip(): valor
            for chave, valor in (d or {}).items()
        }

    def __repr__ (self) -> str:
        return f"<LowerDict com '{len(self)}' chaves>"

    def __getitem__ (self, nome: str) -> T:
        return self.__d[nome.strip().lower()]

    def __setitem__ (self, nome: str, valor: T) -> None:
        self.__d[nome.lower().strip()] = valor

    def __contains__ (self, chave: str) -> bool:
        return chave.lower().strip() in self.__d

    def __len__ (self) -> int:
        return len(self.__d)

    def __bool__ (self) -> bool:
        return bool(self.__d)

    def __iter__ (self) -> Generator[str, None, None]:
        for chave in self.__d:
            yield chave

    def __eq__ (self, other: object) -> bool:
        return False if not isinstance(other, LowerDict) else (
            len(self) == len(other)
            and all(
                chave in other and self[chave] == other[chave]
                for chave in self
            )
        )

    @property
    def __dict__ (self) -> dict[str, T]:
        return self.__d

__all__ = [
    "Email",
    "LowerDict",
    "InfoStack",
    "Diretorio",
    "Resultado",
    "Coordenada",
    "ResultadoSQL",
]
