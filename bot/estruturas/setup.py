# std
from __future__ import annotations
import typing, functools, dataclasses
import inspect, decimal, operator
# interno
from ..sistema import Caminho
# externo
import win32api, win32con

P = typing.ParamSpec("P")

@dataclasses.dataclass
class Coordenada:
    """Coordenada de uma região na tela"""

    x: int
    y: int
    largura: int
    altura: int

    @classmethod
    def tela (cls) -> Coordenada:
        """Coordenada da tela"""
        return Coordenada(
            win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN),
            win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN),
            win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
            win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        )

    @classmethod
    def from_box (cls, box: tuple[int, int, int, int]) -> Coordenada:
        """Criar coordenada a partir de uma `box`
        - `(x-esquerda, y-cima, x-direita, y-baixo)`"""
        x, y = int(box[0]), int(box[1])
        largura, altura = int(box[2] - x), int(box[3] - y)
        return Coordenada(x, y, largura, altura)

    def __iter__ (self) -> typing.Generator[int, None, None]:
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
        return all((
            x >= self.x,
            x <= self.x + self.largura,
            y >= self.y,
            y <= self.y + self.altura
        ))

    def __hash__ (self) -> int:
        return hash(tuple(self))

    def transformar (self, xOffset=0.5, yOffset=0.5) -> tuple[int, int]:
        """Transformar as cordenadas para a posição (X, Y) de acordo com a porcentagem `xOffset` e `yOffset`
        - (X, Y) central caso os offsets não tenham sido informados
        - `xOffset` esquerda, centro, direita = 0.0, 0.5, 1.0
        - `yOffset` topo, centro, baixo = 0.0, 0.5, 1.0"""
        # enforça o range entre 0.0 e 1.0
        xOffset, yOffset = max(0.0, min(1.0, xOffset)), max(0.0, min(1.0, yOffset))
        return (
            int(self.x + self.largura * xOffset),
            int(self.y + self.altura * yOffset)
        )

    def to_box (self) -> tuple[int, int, int, int]:
        """Transformar a coordenada para uma `box`
        - `(x-esquerda, y-cima, x-direita, y-baixo)`"""
        x, y, largura, altura = self
        return (x, y, largura + x, altura + y)

class Resultado [T]:
    """Classe para capturar o `return | Exception` das chamadas

    ```
    # informar a função, os argumentos posicionais e os argumentos nomeados
    # a função será automaticamente chamada após
    resultado = Resultado(funcao, "argumento1", "argumento2", argumento=valor)
    # pode se utilizar como decorador em uma função e obter Resultado como retorno
    @Resultado.decorador

    # representação "sucesso" ou "erro"
    repr(resultado)

    # checar sucesso na chamada
    if resultado: ...
    if resultado.ok()

    # acessando
    valor, erro = resultado.unwrap()
    valor, erro = resultado.valor, resultado.erro
    valor = resultado.valor_ou(default) # valor ou default caso a função tenha apresentado erro
    ```"""

    valor: T | None
    erro: Exception | None

    def __init__(self, funcao: typing.Callable[..., T], *args, **kwargs) -> None:
        self.valor = self.erro = None
        try: self.valor = funcao(*args, **kwargs)
        except Exception as erro: self.erro = erro

    @staticmethod
    def decorador[K] (func: typing.Callable[P, K]) -> typing.Callable[P, Resultado[K]]: # type: ignore
        """Permite que a classe seja utilizada como um decorador
        - Função"""
        def decorador (*args: P.args, **kwargs: P.kwargs) -> Resultado[K]: # type: ignore
            return Resultado(func, *args, **kwargs)
        return decorador

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.erro == None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Resultado[T] {"sucesso" if self else "erro"}>"

    def ok (self) -> bool:
        """Indicação de sucesso"""
        return bool(self)

    def unwrap (self) -> tuple[T, None] | tuple[None, Exception]:
        """Obter `valor, erro` do resultado"""
        return self.valor, self.erro # type: ignore

    def valor_ou[K] (self, default: K) -> T | K:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        return self.valor if self else default # type: ignore

class InfoStack:
    """Informações do `Stack` de execução"""

    caminho: Caminho
    """Caminho do arquivo"""
    funcao: str
    """Nome da função"""
    linha: int
    """Linha do item executado"""

    def __init__ (self, index=1) -> None:
        """Obter informações presente no stack dos callers
        - `Default` arquivo que chamou o `InfoStack()`"""
        frame = inspect.stack()[index]
        self.caminho = Caminho(frame.filename)
        self.linha, self.funcao = frame.lineno, frame.function

    @staticmethod
    def caminhos () -> list[Caminho]:
        """Listar os caminhos dos callers no stack de execução
        - `[0] topo stack`
        - `[-1] começo stack`"""
        return [
            caminho
            for frame in inspect.stack()
            if (caminho := Caminho(frame.filename)).arquivo()
        ]

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
        return f"<LowerDict[T] com '{len(self)}' chave(s)>"

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

    def __iter__ (self) -> typing.Generator[str, None, None]:
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

    def get[K] (self, chave: str, default: T | K = None) -> T | K:
        return self.__d.get(chave.lower().strip(), default)

    def to_dict (self) -> dict[str, T]:
        return self.__d

class Decimal:
    """Classe para realizar comparações e operações matemáticas com precisão em números com ponto flutuante
    - Abstração do pacote std `decimal`
    - `float` não oferece precisão

    ```
    # `valor` aceito no formato int, com casas decimais ou exponencial
    # `precisao` limita a quantidade de casas decimais
    # `separador_decimal` caso o separador das casas decimais seja diferente de `.`
    Decimal("1")
    Decimal("1.2345", 4)
    Decimal("1234.56", 4)
    Decimal("R$ 1.234,56", separador_decimal=",")
    Decimal("1.2345E+2")
    # Pode resultar em "NaN" caso o valor seja inválido
    Decimal("xpto")

    # Transformações aceitas
    str(decimal)
    int(decimal)
    float(decimal)
    bool(decimal)

    # Funções
    abs(decimal)
    round(decimal)

    # Métodos
    decimal.nan()

    # Comparadores | Aceito int str Decimal
    == != < <= > >=

    # Operações | Aceito int str Decimal
    # Pode resultar em "NaN" caso envolva um Decimal("NaN") ou str inválida
    + += - -= * *= / /= // //= % %= ** **=

    # Checar decimal diferente de 0 e "NaN"
    bool(decimal)
    if decimal: ...
    ```"""

    d: decimal.Decimal
    precisao: int
    separador_decimal: str

    def __init__ (self, valor: str,
                        precisao: int = 2,
                        separador_decimal = ".") -> None:
        self.separador_decimal = separador_decimal
        assert precisao >= 1, "A precisão decimal deve ser >= 1"
        self.precisao = precisao

        parte_inteiro, _, parte_decimal = valor.lower().partition(separador_decimal)
        inteiro = "".join(p for p in parte_inteiro if p.isdigit() or p in "+-")
        decimal_ou_exponencial = "".join(p for p in parte_decimal if p.isdigit() or p in "+-e")

        exponent = decimal.Decimal(".".ljust(precisao + 1, "0"))
        valor = inteiro if not decimal_ou_exponencial else f"{inteiro}.{decimal_ou_exponencial}"
        try: self.d = decimal.Decimal(valor).quantize(exponent, decimal.ROUND_FLOOR)
        except Exception: self.d = decimal.Decimal("NaN")

    def __repr__ (self) -> str:
        return f"{type(self).__name__}(valor={str(self)!r}, precisao={self.precisao}, separador_decimal={self.separador_decimal!r})>"

    def __str__ (self) -> str:
        return str(self.d).replace(".", self.separador_decimal)
    def __int__ (self) -> int:
        return int(self.d)
    def __float__ (self) -> float:
        return float(self.d)
    def __bool__ (self) -> bool:
        return not self.nan() and bool(self.d)

    def __abs__ (self) -> Decimal:
        valor_absoluto = str(self.d).removeprefix("-")
        return Decimal(valor_absoluto, self.precisao)
    def __round__ (self, n: int = 0) -> Decimal:
        valor = str(round(self.d, n))
        return Decimal(valor, self.precisao)

    def __comparar (self, other: object, operator: typing.Callable) -> bool:
        match other:
            case str() | int(): return operator(self.d, Decimal(str(other), self.precisao, self.separador_decimal).d)
            case Decimal():     return operator(self.d, other.d)
            case _:             return NotImplemented
    def __eq__ (self, other: object) -> bool: return self.__comparar(other, operator.eq)
    def __ne__ (self, other: object) -> bool: return self.__comparar(other, operator.ne)
    def __lt__ (self, other: object) -> bool: return self.__comparar(other, operator.lt)
    def __le__ (self, other: object) -> bool: return self.__comparar(other, operator.le)
    def __gt__ (self, other: object) -> bool: return self.__comparar(other, operator.gt)
    def __ge__ (self, other: object) -> bool: return self.__comparar(other, operator.ge)

    def __aplicar (self, other: object, operator: typing.Callable) -> Decimal:
        obj = object.__new__(Decimal)
        match other:
            case str() | int(): obj.d = operator(self.d, Decimal(str(other), self.precisao, self.separador_decimal).d)
            case Decimal():     obj.d = operator(self.d, other.d)
            case _:             return NotImplemented

        exponent = decimal.Decimal(".".ljust(self.precisao + 1, "0"))
        obj.d = obj.d.quantize(exponent, decimal.ROUND_FLOOR)
        obj.precisao = self.precisao
        obj.separador_decimal = self.separador_decimal

        return obj
    def __add__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.add)
    def __iadd__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.iadd)
    def __sub__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.sub)
    def __isub__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.isub)
    def __mul__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.mul)
    def __imul__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.imul)
    def __mod__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.mod)
    def __imod__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.imod)
    def __pow__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.pow)
    def __ipow__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.ipow)
    def __truediv__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.truediv)
    def __itruediv__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.itruediv)
    def __floordiv__  (self, other: object) -> Decimal: return self.__aplicar(other, operator.floordiv)
    def __ifloordiv__ (self, other: object) -> Decimal: return self.__aplicar(other, operator.ifloordiv)

    def nan (self) -> bool:
        """Checar se o decimal não é um número"""
        return self.d.is_nan()

    @staticmethod
    def sum (decimais: typing.Iterable[Decimal]) -> Decimal:
        """Realizar o `sum()` de todos os `decimais`"""
        return functools.reduce(lambda total, atual: total + atual,
                                decimais)

__all__ = [
    "Caminho",
    "Decimal",
    "LowerDict",
    "InfoStack",
    "Resultado",
    "Coordenada",
]