# std
from __future__ import annotations
import typing, collections, random
# interno
from bot.formatos import stringify
from bot.estruturas.string import String
# externo
import win32api, win32con

class Coordenada:
    """Coordenada de uma região retangular na tela baseado nos pixels
    - `x` Posição horizontal do canto superior esquerdo
    - `y` Posição vertical do canto superior esquerdo
    - `largura` Largura da área, a partir do `x`
    - `altura` Altura da área, a partir do `y`"""

    x: int
    y: int
    largura: int
    altura: int

    def __init__ (self, x: int, y: int, largura: int, altura: int) -> None:
        self.x, self.y, self.largura, self.altura = map(int, (x, y, largura, altura))

    @classmethod
    def Tela (cls) -> Coordenada:
        """Coordenada da tela"""
        return Coordenada(
            win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN),
            win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN),
            win32api.GetSystemMetrics(win32con.SM_CXSCREEN) - 1,
            win32api.GetSystemMetrics(win32con.SM_CYSCREEN) - 1,
        )

    @classmethod
    def FromBox (cls, box: tuple[int, int, int, int]) -> Coordenada:
        """Criar coordenada a partir de uma `box`
        - `(x-esquerda, y-cima, x-direita, y-baixo)`"""
        x, y = box[0], box[1]
        largura, altura = box[2] - x, box[3] - y
        return Coordenada(x, y, largura, altura)

    def __repr__ (self) -> str:
        return f"<Coordenada(x={self.x}, y={self.y}, largura={self.largura}, altura={self.altura})>"

    def __eq__ (self, value: object) -> bool:
        return self.__dict__ == value.__dict__  if isinstance(value, Coordenada) else False

    def __len__ (self) -> int:
        return 4

    def __bool__ (self) -> bool:
        return 0 not in (self.altura, self.largura)

    def __iter__ (self) -> typing.Generator[int, None, None]:
        """Utilizado com o `tuple(coordenada)` e `x, y, largura, altura = coordenada`"""
        yield self.x
        yield self.y
        yield self.largura
        yield self.altura

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

    def __iadd__ (self, value: object) -> Coordenada:
        """Adicionar o `X, Y` da coordenada de `value`
        - Útil para transformar regiões de imagens para a tela"""
        if not isinstance(value, Coordenada):
            return NotImplemented
        self.x += value.x
        self.y += value.y
        return self

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

    def topo (self) -> tuple[int, int]:
        """Posição do topo central
        - O mesmo que `self.transformar(0.5, 0.01)`"""
        return self.transformar(0.5, 0.01)

    def centro (self) -> tuple[int, int]:
        """Posição central
        - O mesmo que `self.transformar(0.5, 0.5)`"""
        return self.transformar(0.5, 0.5)

    def base (self) -> tuple[int, int]:
        """Posição da base central
        - O mesmo que `self.transformar(0.5, 0.99)`"""
        return self.transformar(0.5, 0.99)

    def random (self) -> tuple[int, int]:
        """Retorna um ponto aleatório dentro da região"""
        return (random.randint(self.x, self.x + self.largura - 1),
                random.randint(self.y, self.y + self.altura - 1))

class DictNormalizado[T] (collections.UserDict[str, T]):
    """Dicionário que armazena e acessa chaves sempre na forma `String(chave).normalizar()`

    Esta classe estende o `dict` padrão do Python para garantir que todas as
    operações envolvendo chaves (inserção, acesso, remoção e verificação)
    utilizem automaticamente a versão normalizada da chave"""

    def __init__ (self, d: typing.Mapping[str, T] | None = None) -> None:
        super().__init__()
        if not d: return
        for chave, valor in d.items():
            self[chave] = valor

    def __str__ (self) -> str:
        return str(self.data)

    def __repr__ (self) -> str:
        return f"<DictNormalizado[T] com {len(self)} chave(s)>"

    @property
    def __dict__ (self) -> dict[str, T]: # type: ignore
        return self.data

    def __getitem__ (self, chave: str) -> T:
        return super().__getitem__(str(String(chave).normalizar()))

    def __setitem__ (self, chave: str, valor: T) -> None:
        super().__setitem__(str(String(chave).normalizar()), valor)

    def __delitem__ (self, chave: str) -> None:
        super().__delitem__(str(String(chave).normalizar()))

    def __contains__ (self, chave: object) -> bool:
        return (
            False if not isinstance(chave, str)
            else super().__contains__(str(String(chave).normalizar()))
        )

    def stringify (self, indentar: bool = False) -> str:
        """Transformar para um objeto json"""
        return stringify(self.data, indentar=indentar)

__all__ = [
    "Coordenada",
    "DictNormalizado",
]