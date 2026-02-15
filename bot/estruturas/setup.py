# std
from __future__ import annotations
import typing
# interno
from bot.sistema import Caminho
# externo
import win32api, win32con

P = typing.ParamSpec("P")

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
    def tela (cls) -> Coordenada:
        """Coordenada da tela"""
        return Coordenada(
            win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN),
            win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN),
            win32api.GetSystemMetrics(win32con.SM_CXSCREEN) - 1,
            win32api.GetSystemMetrics(win32con.SM_CYSCREEN) - 1,
        )

    @classmethod
    def from_box (cls, box: tuple[int, int, int, int]) -> Coordenada:
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

class Resultado [T]:
    """Classe para capturar o `return | Exception` de chamadas de uma função
    - Alternativa para não propagar o erro e nem precisar utilizar `try-except`

    ```
    # Criando com a função, argumentos posicionais e argumentos nomeados
    # a função será automaticamente chamada após
    resultado = Resultado(funcao, "argumento1", "argumento2", argumento=valor)
    # Pode se utilizar como decorador em uma função e obter Resultado como retorno
    @Resultado.decorador

    # Representação "sucesso" ou "erro"
    repr(resultado)

    # Checar sucesso na chamada
    if resultado: ...
    if resultado.ok()

    # Validação com mensagem de erro
    resultado.validar("Erro ao realizar xpto")
    valor = resultado.validar("Erro ao realizar xpto").valor()

    # Acessar
    valor = resultado.valor()           # necessário checar se é de sucesso
    erro = resultado.erro()             # necessário checar se é de erro
    valor = resultado.valor_ou(default) # valor ou default caso o resultado seja de erro

    # Mapear o resultado para outra função
    Resultado(lambda: 10).map(lambda x: x * 2)  # Sucesso; valor=20
    Resultado(lambda: 1/0).map(lambda x: x * 2) # Erro; ZeroDivisionError
    ```"""

    __valor: T | None
    __erro: Exception | None

    def __init__(self, funcao: typing.Callable[..., T], *args, **kwargs) -> None:
        self.__valor = self.__erro = None
        try: self.__valor = funcao(*args, **kwargs)
        except Exception as erro: self.__erro = erro

    @staticmethod
    def decorador[K] (func: typing.Callable[P, K]) -> typing.Callable[P, Resultado[K]]: # type: ignore
        """Permite que a classe seja utilizada como um decorador
        - Função"""
        def decorador (*args: P.args, **kwargs: P.kwargs) -> Resultado[K]: # type: ignore
            return Resultado(func, *args, **kwargs)
        return decorador

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.__erro == None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Resultado[T] {"sucesso" if self else "erro"}>"

    def ok (self) -> bool:
        """Indicação de sucesso"""
        return bool(self)

    def valor (self) -> T:
        """Obter o `valor` do resultado
        - Necessário validar se o resultado é de sucesso"""
        if not self.ok():
            raise Exception(f"Tentado obter o valor de um resultado sem sucesso") from self.__erro
        return self.__valor # type: ignore

    def erro (self) -> Exception:
        """Obter o `erro` do resultado
        - Necessário validar se o resultado é de erro"""
        if self.ok():
            raise Exception(f"Tentado obter o erro de um resultado com sucesso")
        return self.__erro # type: ignore

    def valor_ou[D] (self, default: D) -> T | D:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        return self.__valor if self else default # type: ignore

    def validar (self, mensagem: str) -> typing.Self:
        """Validar se o resultado é de sucesso
        - `Exception(mensagem; erro)` caso não seja um resultado de sucesso
        - Retornado `self` para encadeamento"""
        if not self.ok():
            raise Exception(f"{mensagem}; {self.__erro}")
        return self

    def map[K] (self, func: typing.Callable[[T], K], *args, **kwargs) -> Resultado[K]: # type: ignore
        """Aplicar o `valor` do resultado na `func` como primeiro argumento e retornar um novo resultado
        - `args` e `kwargs` para adicionar mais argumentos caso necessário
        - Caso seja resultado de erro, retornado o mesmo resultado para propagar o erro"""
        if not self.ok(): return self # type: ignore
        return Resultado(func, self.__valor, *args, **kwargs)

class LowerDict [T]:
    """Classe usada para obter/adicionar/remover chaves de um `dict` como `lower-case`
    - Obter: `LowerDict["nome"]` KeyError caso não exista
    - Checar existência: `"nome" in LowerDict`
    - Adicionar/Atualizar: `LowerDict["nome"] = "valor"`
    - Remover: `del LowerDict["nome"]`
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
    
    def __delitem__ (self, chave: str) -> None:
        del self.__d[chave.lower().strip()]

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

__all__ = [
    "Caminho",
    "LowerDict",
    "Resultado",
    "Coordenada",
]