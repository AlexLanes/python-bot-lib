# std
from __future__ import annotations
import typing, functools, decimal, operator

class Decimal:
    """Classe para realizar comparações e operações matemáticas com precisão em números com ponto flutuante
    - Abstração do pacote std `decimal`
    - `float` possuiu precisão limitada

    ```
    # `valor` aceito como `str`, com ou sem casas decimais ou exponencial
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

    def copiar (self, separador: str | None = None,
                      precisao: int | None = None) -> Decimal:
        """Criar um cópia do objeto
        - `separador` para alterar o separador decimal
        - `precisao` para alterar a precisão decimal"""
        copia = Decimal(str(self), precisao or self.precisao, self.separador_decimal)
        if separador: copia.separador_decimal = separador
        return copia

    @staticmethod
    def sum (decimais: typing.Iterable[Decimal]) -> Decimal:
        """Realizar o `sum()` de todos os `decimais`"""
        return functools.reduce(lambda total, atual: total + atual,
                                decimais)
