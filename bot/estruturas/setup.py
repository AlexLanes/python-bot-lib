# std
from __future__ import annotations
import typing, inspect, dataclasses
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
        return hash(str(tuple(self)))

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
    """Classe para capturar o resultado ou `Exception` de alguma chamada

    ```
    # informar a função, os argumentos posicionais e os argumentos nomeados
    # a função será automaticamente chamada após
    resultado = Resultado(funcao, "nome", "idade", key=value)
    # pode se utilizar como decorador em uma função e obter Resultado como retorno
    @Resultado.decorador

    # representação "sucesso" ou "erro"
    repr(resultado)

    # checar sucesso na chamada
    bool(resultado) | if resultado: ...

    # acessando
    valor, erro = resultado.unwrap()
    valor = resultado.valor() # erro caso a função tenha apresentado erro
    valor = resultado.valor_ou(default) # valor ou default caso a função tenha apresentado erro
    ```"""

    __valor: T | None
    __erro: Exception | None

    def __init__ (self, funcao: typing.Callable[..., T],
                        *args: typing.Any,
                        **kwargs: typing.Any) -> None:
        self.__valor = self.__erro = None
        try: self.__valor = funcao(*args, **kwargs)
        except Exception as erro: self.__erro = erro

    @staticmethod
    def decorador[D] (func: typing.Callable[P, D]) -> typing.Callable[P, Resultado[D]]: # type: ignore
        """Permite que a classe seja utilizada como um decorador
        - Função"""
        def decorador (*args: P.args, **kwargs: P.kwargs) -> Resultado[D]: # type: ignore
            return Resultado(func, *args, **kwargs)
        return decorador

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.__erro == None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Resultado[T] {"sucesso" if self else "erro"}>"

    def unwrap (self) -> tuple[T, None] | tuple[None, Exception]:
        """Realizar unwrap do `valor, erro = resultado.unwrap()`"""
        return self.__valor, self.__erro # type: ignore

    def valor (self) -> T:
        """Obter o valor do resultado
        - `raise Exception` caso tenha apresentado erro"""
        if self.__erro != None:
            self.__erro.add_note("Valor não presente no resultado")
            raise self.__erro
        return self.__valor # type: ignore

    def valor_ou[K] (self, default: K) -> T | K:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        return self.__valor if self else default # type: ignore

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

    def to_dict (self) -> dict[str, T]:
        return self.__d

__all__ = [
    "LowerDict",
    "InfoStack",
    "Resultado",
    "Coordenada",
]