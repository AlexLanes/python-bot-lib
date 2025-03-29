# std
from __future__ import annotations
from datetime import datetime as Datetime
import os, typing, pathlib, shutil, inspect, dataclasses
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

class Caminho:
    """Classe para representação de caminhos, em sua versão absoluta, 
    do sistema operacional e manipulação de arquivos/pastas

    - Criação: `Caminho("caminho_completo")`, `Caminho(".", "pasta", "arquivo.txt")` ou `Caminho.diretorio_execucao()`
    - Acesso: `Caminho().string` ou `str(Caminho())`
    - Concatenação: `Caminho() + "pasta" + "arquivo"` ou `Caminho() / "pasta" / "arquivo"`
    - Iteração sobre diretório: `for caminho in Caminho(): ...`
    - Demais métodos/atributos estão comentados"""

    path: pathlib.Path

    def __init__ (self, *fragmento: str) -> None:
        self.path = pathlib.Path(*fragmento).resolve()

    @classmethod
    def diretorio_execucao (cls) -> Caminho:
        """Obter o caminho para o diretório de execução atual"""
        caminho = object.__new__(cls)
        caminho.path = pathlib.Path.cwd().resolve()
        return caminho

    @classmethod
    def diretorio_usuario (cls) -> Caminho:
        """Obter o caminho para o diretório do usuário atual"""
        caminho = object.__new__(cls)
        caminho.path = pathlib.Path.home().resolve()
        return caminho

    def __repr__ (self) -> str:
        return f"<Caminho '{self.path}'>"

    def __str__ (self) -> str:
        return str(self.path)

    def __add__ (self, fragmento: str) -> Caminho:
        return Caminho(self.string, str(fragmento))

    def __truediv__ (self, fragmento: str) -> Caminho:
        return self + fragmento

    def __iter__ (self) -> typing.Generator[Caminho, None, None]:
        if not self.diretorio():
            return
        for p in self.path.iterdir():
            yield Caminho(str(p))

    def __eq__ (self, value: object) -> bool:
        caminho = value.string if isinstance(value, Caminho) else str(value)
        return self.string == caminho

    def __hash__ (self) -> int:
        return hash(self.string)

    @property
    def string (self) -> str:
        """Obter o caminho como string
        - Versão alternativa: str(caminho)"""
        return str(self)

    @property
    def parente (self) -> Caminho:
        """Obter o caminho para o parente do caminho atual"""
        return Caminho(str(self.path.parent))

    @property
    def nome (self) -> str:
        """Nome final do caminho"""
        return self.path.name

    @property
    def fragmentos (self) -> list[str]:
        """Fragmentos ordenados do caminho"""
        return list(self.path.parts)

    @property
    def data_criacao (self) -> Datetime:
        """Data de criação do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe():
            raise ValueError(f"{self} inexistente")
        return Datetime.fromtimestamp(os.path.getctime(self.path))

    @property
    def data_modificao (self) -> Datetime:
        """Data da última modificação do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe():
            raise ValueError(f"{self} inexistente")
        return Datetime.fromtimestamp(os.path.getmtime(self.path))

    @property
    def tamanho (self) -> int:
        """Tamanho em bytes do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe():
            raise ValueError(f"{self} inexistente")
        return os.path.getsize(self.path) if not self.diretorio() else sum(
            os.path.getsize(caminho.path) if not self.diretorio() else caminho.tamanho
            for caminho in self
        )

    def existe (self) -> bool:
        """Checar se o caminho existe"""
        return self.path.exists()

    def arquivo (self) -> bool:
        """Checar se o caminho existente é de um arquivo"""
        return self.path.is_file()

    def diretorio (self) -> bool:
        """Checar se o caminho existente é de um diretório"""
        return self.path.is_dir()

    def copiar (self, diretorio: Caminho) -> Caminho:
        """Copiar o arquivo ou diretório do caminho atual para o `diretorio` e retornar o caminho
        - Sobrescreve os arquivos existentes (recursivamente se for diretório)
        - Não tem efeito caso caminho não exista"""
        destino = diretorio.criar_diretorios() / self.nome
        if self.arquivo():
            shutil.copyfile(self.path, destino.path)
        elif self.diretorio():
            shutil.copytree(self.path, destino.path, dirs_exist_ok=True)
        return destino

    def renomear (self, novo_nome: str) -> Caminho:
        """Renomear o nome final do caminho para `novo_nome` e retornar o caminho
        - Sobrescreve os arquivos existentes (recursivamente se for diretório)
        - Não tem efeito caso caminho não exista"""
        destino = self.parente / os.path.basename(novo_nome)
        if self.arquivo():
            shutil.copyfile(self.path, destino.path)
            self.apagar_arquivo()
        elif self.diretorio():
            shutil.copytree(self.path, destino.path, dirs_exist_ok=True)
            self.apagar_diretorio()
        return destino

    def mover (self, diretorio: Caminho) -> Caminho:
        """Mover o arquivo ou diretório do caminho atual para o `diretorio` e retornar o caminho
        - Sobrescreve os arquivos existentes (recursivamente se for diretório)
        - Não tem efeito caso caminho não exista"""
        destino = self.copiar(diretorio)
        self.apagar_diretorio() if self.diretorio() else self.apagar_arquivo()
        return destino

    def criar_diretorios (self) -> typing.Self:
        """Criar todos os diretórios no caminho atual que não existem
        - Não altera diretórios existentes"""
        if not self.existe(): self.path.mkdir(parents=True)
        return self

    def apagar_arquivo (self) -> Caminho:
        """Apagar o arquivo do caminho atual e retornar ao parente
        - Não tem efeito caso não exista ou não seja arquivo"""
        if self.existe() and not self.diretorio():
            self.path.unlink()
        return self.parente

    def apagar_diretorio (self) -> Caminho:
        """Apagar o diretório e conteúdo do caminho atual e retornar ao parente
        - Não tem efeito caso não exista ou não seja diretório"""
        if self.diretorio():
            for caminho in self:
                caminho.apagar_diretorio() if caminho.diretorio() else caminho.apagar_arquivo()
            self.path.rmdir()
        return self.parente

    def procurar (self, filtro: typing.Callable[[Caminho], bool], recursivo=False) -> list[Caminho]:
        """Procurar caminhos de acordo com o `filtro`
        - `recursivo` indicador para percorrer os diretórios filhos
        - Não tem efeito caso não exista ou não seja diretório"""
        glob = self.path.rglob if recursivo else self.path.glob
        return [
            caminho
            for path in glob("*")
            if filtro(caminho := Caminho(str(path)))
        ]

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
    "Caminho",
    "LowerDict",
    "InfoStack",
    "Resultado",
    "Coordenada",
]