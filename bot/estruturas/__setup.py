# std
from __future__ import annotations
from inspect import stack
from dataclasses import dataclass
from typing import Generator, Callable
from datetime import datetime as Datetime
from itertools import tee as duplicar_iterable
from os.path import getmtime as ultima_alteracao
# interno
import bot
# externo
from polars import DataFrame

@dataclass
class Coordenada:
    """Coordenada de uma região na tela"""
    x: int
    y: int
    largura: int
    altura: int

    def __iter__ (self):
        """Utilizado com o `tuple(coordenada)` e `x, y, largura, altura = coordenada`"""
        yield self.x
        yield self.y
        yield self.largura
        yield self.altura

    def __len__ (self):
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
    """Classe utilizada no retorno da execução do banco de dados"""
    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica para o comando sql"""
    colunas: tuple[str, ...]
    """Colunas das linhas retornadas (se houver)"""
    linhas: Generator[tuple[bot.tipagem.tipoSQL, ...], None, None]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    def __iter__ (self) -> Generator[tuple[bot.tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    def __repr__ (self) -> str:
        "Representação da classe"
        possui_linhas = False
        self.linhas, linhas = duplicar_iterable(self.linhas)
        try: possui_linhas = bool(next(linhas))
        except: pass

        tipo = f"com {self.linhas_afetadas} linha(s) afetada(s)" if self.linhas_afetadas \
          else f"com {len(self.colunas)} coluna(s) e {len(self)} linha(s)" if possui_linhas \
          else f"vazio"

        return f"<ResultadoSQL {tipo}>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return "vazio" not in repr(self)

    def __len__ (self) -> int:
        """Obter a quantidade de linhas no retornadas"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        return sum(1 for _ in linhas)

    def __getitem__ (self, campo: str) -> bot.tipagem.tipoSQL:
        """Obter um campo da primeira linha"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        linha = next(linhas)
        return linha[self.colunas.index(campo)]

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
    """Classe `genérica` de utilização para retornar resultado ou erro de alguma chamada"""
    __valor: T | None
    __erro: Exception | None

    def __init__ (self, funcao: Callable[[], T], *args, **kwargs) -> None:
        """Realizar a chamada na `função` com os argumentos `args` e `kwargs`"""
        try:
            self.__valor = funcao(*args, **kwargs)
            self.__erro = None
        except Exception as erro:
            bot.logger.alertar(f"Função '{funcao.__name__}' executada pelo <Resultado[T]> apresentou erro")
            self.__valor = None
            self.__erro = erro

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.__erro == None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Resultado[T] {"com" if self else "sem"} valor>"

    def valor (self) -> T:
        """Obter o valor do resultado
        - `raise Exception` caso tenha apresentado erro"""
        if not self:
            self.__erro.add_note("Valor não presente no resultado")
            raise self.__erro
        return self.__valor

    def valor_ou (self, default: T) -> T:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        if not self: return default
        return self.__valor

@dataclass
class Diretorio:
    """Armazena os caminhos de pastas e arquivos presentes no diretório"""
    caminho: bot.tipagem.caminho
    """Caminho absoluto do diretorio"""
    pastas: list[bot.tipagem.caminho]
    """Lista contendo o caminho de cada pasta do diretório"""
    arquivos: list[bot.tipagem.caminho]
    """Lista contendo o caminho de cada arquivo do diretório"""

    def __repr__ (self) -> str:
        return f"<Diretorio '{self.caminho}' com {len(self.pastas)} pasta(s) e {len(self.arquivos)} arquivos(s)>"

    def query_data_alteracao_arquivos (self,
                                       inicio=Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                       fim=Datetime.now()) -> list[tuple[bot.tipagem.caminho, Datetime]]:
        """Consultar arquivos do diretório com base na data de alteração
        - Default: Hoje
        - Retorna uma lista `(caminho, data)` ordenado pelos mais antigos"""
        ordenar_antigos = lambda x: x[1]
        criar_data = lambda caminho: Datetime.fromtimestamp(ultima_alteracao(caminho))

        arquivos = [(caminho, data) for caminho in self.arquivos
                    if inicio <= (data := criar_data(caminho)) <= fim]
        arquivos.sort(key=ordenar_antigos)

        return arquivos

class InfoStack:
    """Informações do `Stack` de execução"""
    nome: str
    """Nome do arquivo"""
    funcao: str
    """Nome da função"""
    linha: int
    """Linha do item executado"""
    caminho: bot.tipagem.caminho
    """Caminho do arquivo"""

    def __init__ (self, index=1) -> None:
        """Obter informações presente no stack dos callers
        - `Default` arquivo que chamou o `InfoStack()`"""
        frame = stack()[index]
        self.linha, self.funcao = frame.lineno, frame.function
        self.nome = bot.windows.nome_base(frame.filename)
        self.caminho = bot.windows.nome_diretorio(frame.filename)

    @staticmethod
    def caminhos () -> list[bot.tipagem.caminho]:
        """Listar os caminhos dos callers no stack de execução
        - `[0] topo stack`
        - `[-1] começo stack`"""
        return [
            bot.windows.caminho_absoluto(frame.filename)
            for frame in stack()
            if bot.windows.afirmar_arquivo(frame.filename)
        ]

@dataclass
class Email:
    """Classe para armazenar informações extraídas de Email"""
    uid: int
    """id do e-mail"""
    remetente: bot.tipagem.email
    """Remetente que enviou o e-mail"""
    destinatarios: list[bot.tipagem.email]
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

__all__ = [
    "Email",
    "InfoStack",
    "Diretorio",
    "Resultado",
    "Coordenada",
    "ResultadoSQL",
]
