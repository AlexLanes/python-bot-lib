# std
from __future__ import annotations
from datetime import datetime as Datetime
import os, typing, pathlib, shutil, inspect, itertools, functools, dataclasses
# interno
from .. import tipagem
# externo
from polars import DataFrame

@dataclasses.dataclass
class Coordenada:
    """Coordenada de uma região na tela"""

    x: int
    y: int
    largura: int
    altura: int

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

@dataclasses.dataclass
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
    linhas: typing.Generator[tuple[tipagem.tipoSQL, ...], None, None]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    def __iter__ (self) -> typing.Generator[tuple[tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    @functools.cached_property
    def __p (self) -> tuple[tipagem.tipoSQL, ...] | None:
        """Cache da primeira linha no resultado
        - `None` caso não possua"""
        self.linhas, linhas = itertools.tee(self.linhas)
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
        self.linhas, linhas = itertools.tee(self.linhas)
        return sum(1 for _ in linhas)

    def __getitem__ (self, campo: str) -> tipagem.tipoSQL:
        """Obter o `campo` da primeira linha"""
        return self.__p[self.colunas.index(campo)]

    @property
    def __dict__ (self) -> dict[str, int | None | list[dict]]:
        """Representação formato dicionário"""
        self.linhas, linhas = itertools.tee(self.linhas)
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
        self.linhas, linhas = itertools.tee(self.linhas)
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

    def __init__ (self, funcao: typing.Callable[..., T], *args, **kwargs) -> None:
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

class Caminho:
    """Classe para representação de caminhos, em sua versão absoluta, 
    do sistema operacional e manipulação de arquivos/pastas

    - Criação: `Caminho("caminho_completo")`, `Caminho(".", "pasta", "arquivo.txt")` ou `Caminho.diretorio_execucao()`
    - Acesso: `Caminho().string` ou `str(Caminho())`
    - Concatenação: `Caminho() + "pasta" + "arquivo"` ou `Caminho() / "pasta" / "arquivo"`
    - Iteração sobre diretório: `for caminho in Caminho(): ...`
    - Demais métodos/atributos estão comentados"""

    __p: pathlib.Path

    def __init__ (self, *fragmento: str) -> None:
        self.__p = pathlib.Path(*fragmento).resolve()

    @classmethod
    def diretorio_execucao (cls) -> Caminho:
        """Obter o caminho para o diretório de execução atual"""
        caminho = object.__new__(cls)
        caminho.__p = pathlib.Path.cwd()
        return caminho

    def __repr__ (self) -> str:
        return f"<Caminho '{self.__p}'>"

    def __str__ (self) -> str:
        return str(self.__p)

    def __add__ (self, fragmento: str) -> Caminho:
        return Caminho(self.string, os.path.basename(str(fragmento)))

    def __truediv__ (self, fragmento: str) -> Caminho:
        return self + fragmento

    def __iter__ (self) -> typing.Generator[Caminho, None, None]:
        if not self.diretorio():
            return
        for p in self.__p.iterdir():
            yield Caminho(p)

    @property
    def string (self) -> str:
        """Obter o caminho como string
        - Versão alternativa: str(caminho)"""
        return str(self)

    @property
    def parente (self) -> Caminho:
        """Obter o caminho para o parente do caminho atual"""
        return Caminho(self.__p.parent)

    @property
    def nome (self) -> str:
        """Nome final do caminho"""
        return self.__p.name

    @property
    def fragmentos (self) -> list[str]:
        """Fragmentos ordenados do caminho"""
        return list(self.__p.parts)

    @property
    def data_criacao (self) -> Datetime:
        """Data de criação do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe():
            raise ValueError(f"{self} inexistente")
        return Datetime.fromtimestamp(os.path.getctime(self.__p))

    @property
    def data_modificao (self) -> Datetime:
        """Data da última modificação do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe():
            raise ValueError(f"{self} inexistente")
        return Datetime.fromtimestamp(os.path.getmtime(self.__p))

    @property
    def tamanho (self) -> int:
        """Tamanho em bytes do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe():
            raise ValueError(f"{self} inexistente")
        return os.path.getsize(self.__p) if not self.diretorio() else sum(
            os.path.getsize(caminho.__p) if not self.diretorio() else caminho.tamanho
            for caminho in self
        )

    def existe (self) -> bool:
        """Checar se o caminho existe"""
        return self.__p.exists()

    def arquivo (self) -> bool:
        """Checar se o caminho existente é de um arquivo"""
        return self.__p.is_file()

    def diretorio (self) -> bool:
        """Checar se o caminho existente é de um diretório"""
        return self.__p.is_dir()

    def renomear (self, novo_nome: str, apagar_existente=False) -> Caminho:
        """Renomear o nome final do caminho atual para `novo_nome` e retornar o caminho
        - `apagar_existente` indicador para apagar arquivo ou diretório de `novo_nome`, caso exista, se não `Exception`
        - Não tem efeito caso caminho não exista"""
        novo_nome = os.path.basename(novo_nome)
        caminho = self.parente / novo_nome
        if self.existe():
            if apagar_existente and caminho.existe():
                caminho.apagar_diretorio() if caminho.diretorio() else caminho.apagar_arquivo()
            self.__p.rename(caminho.string)
        return caminho

    def copiar (self, diretorio: Caminho) -> Caminho:
        """Copiar o arquivo ou diretório do caminho atual para o `diretorio` existente
        - Não tem efeito caso algum caminho não exista"""
        destino = diretorio / self.nome
        if self.arquivo() and diretorio.diretorio():
            shutil.copyfile(self.__p, destino.__p)
        elif self.diretorio() and diretorio.diretorio():
            shutil.copytree(self.__p, destino.__p, dirs_exist_ok=True)
        return destino

    def mover (self, diretorio: Caminho) -> Caminho:
        """Mover o arquivo ou diretório do caminho atual para o `diretorio` existente
        - Não tem efeito caso algum caminho não exista"""
        if self.existe() and diretorio.diretorio():
            shutil.move(self.__p, diretorio.__p)
        return diretorio / self.nome

    def criar_diretorios (self) -> typing.Self:
        """Criar todos os diretórios no caminho atual que não existem
        - Não altera diretórios existentes"""
        if not self.existe(): self.__p.mkdir(parents=True)
        return self

    def apagar_arquivo (self) -> Caminho:
        """Apagar o arquivo do caminho atual e retornar ao parente
        - Não tem efeito caso não exista ou não seja arquivo"""
        if self.arquivo(): self.__p.unlink()
        return self.parente

    def apagar_diretorio (self) -> Caminho:
        """Apagar o diretório e conteúdo do caminho atual e retornar ao parente
        - Não tem efeito caso não exista ou não seja diretório"""
        for caminho in self:
            if caminho.arquivo(): caminho.apagar_arquivo()
            elif caminho.diretorio(): caminho.apagar_diretorio()
        if self.diretorio(): self.__p.rmdir()
        return self.parente

    def procurar (self, filtro: typing.Callable[[Caminho], bool], recursivo=False) -> list[Caminho]:
        """Procurar caminhos de acordo com o `filtro`
        - `recursivo` indicador para percorrer os diretórios filhos
        - Não tem efeito caso não exista ou não seja diretório"""
        glob = self.__p.rglob if recursivo else self.__p.glob
        return [
            caminho
            for path in glob("*")
            if filtro(caminho := Caminho(path))
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

@dataclasses.dataclass
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

    @property
    def __dict__ (self) -> dict[str, T]:
        return self.__d

__all__ = [
    "Email",
    "Caminho",
    "LowerDict",
    "InfoStack",
    "Resultado",
    "Coordenada",
    "ResultadoSQL",
]
