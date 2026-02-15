# std
from __future__ import annotations
import typing, pathlib, shutil, mimetypes, functools
from datetime import datetime as Datetime
# interno
from bot.tipagem import SupportsBool

mimetypes.add_type("text/log", ".log")
mimetypes.add_type("application/x-jsonlines", ".jsonl")

class Mimetype:
    """Classe de representação de um `mimetype`"""

    texto: str

    def __init__ (self, texto: str) -> None:
        self.texto = texto

    def __repr__ (self) -> str:
        return f"<Mimetype '{self.texto}'>"

    def __str__ (self) -> str:
        return self.texto

    @functools.cached_property
    def tipo (self) -> str:
        """Tipo principal do `Mimetype`"""
        return self.texto.split("/", 1)[0]

    @functools.cached_property
    def subtipo (self) -> str:
        """Tipo secundário do `Mimetype`"""
        return self.texto.split("/", 1)[1]

class Caminho:
    """Classe para representação de caminhos do sistema operacional e manipulação de arquivos/diretórios
    - Caminhos são tratados internamento em sua verão absoluta
    - Todos os métodos e atributos possuem descrição do que representam

    ### Criação
        - `Caminho("C:/caminho/completo")`
        - `Caminho(".", "pasta", "arquivo.txt")`
        - `Caminho() / "diretorio" / "arquivo.txt"`
        - `Caminho.diretorio_usuario()`, `Caminho.diretorio_execucao()`
    ### Acesso
        - `c.string`, `str(c)`
        - `c.nome`, `c.prefixo`, `c.sufixo`
        - `c.parente`, `c.fragmentos`
    ### Informação
        - `c.existe()`, `c.arquivo()`, `c.diretorio()`
        - `c.tamanho`, `c.data_criacao`, `c.data_modificao`
    ### Iteração sobre Diretório
        - `for caminho in Caminho(): ...`
        - `c.procurar()`
    ### Alteração no Nome do Caminho:
        - `c.com_nome()`
        - `c.com_prefixo()`
        - `c.com_sufixo()`
    ### Modificação no Sistema
        - `c.renomear()`, `c.copiar()`, `c.mover()`
        - `c.apagar_arquivo()`, `c.apagar_diretorio()`
        - `c.criar_diretorios()`, `c.limpar_diretorio()`
    """

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

    @classmethod
    def from_path (cls, path: pathlib.Path) -> Caminho:
        caminho = object.__new__(cls)
        caminho.path = path.resolve()
        return caminho

    def __repr__ (self) -> str:
        return f"<Caminho '{self.path}'>"

    def __str__ (self) -> str:
        return str(self.path)

    def __truediv__ (self, fragmento: str) -> Caminho:
        return Caminho(self.string, str(fragmento))

    def __iter__ (self) -> typing.Generator[Caminho, None, None]:
        if not self.diretorio():
            return
        for p in self.path.iterdir():
            yield Caminho.from_path(p)

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
        return Caminho.from_path(self.path.parent)

    @property
    def nome (self) -> str:
        """Nome final do caminho
        - Para arquivos, retornado o nome + extensao"""
        return self.path.name

    @property
    def prefixo (self) -> str:
        """Nome final do caminho sem o sufixo
        - Para arquivos, retornado o nome sem a extensao"""
        return self.path.stem

    @property
    def sufixo (self) -> str:
        """Nome final do caminho sem o prefixo
        - Para arquivos, retornado apenas a extensao"""
        return self.path.suffix

    @property
    def fragmentos (self) -> list[str]:
        """Fragmentos ordenados do caminho"""
        return list(self.path.parts)

    @property
    def data_criacao (self) -> Datetime:
        """Data de criação do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe(): raise ValueError(f"{self} inexistente")
        return Datetime.fromtimestamp(self.path.stat().st_birthtime)

    @property
    def data_modificao (self) -> Datetime:
        """Data da última modificação do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe(): raise ValueError(f"{self} inexistente")
        return Datetime.fromtimestamp(self.path.stat().st_mtime)

    @property
    def tamanho (self) -> int:
        """Tamanho, em bytes, do arquivo ou diretório
        - `ValueError` caso o caminho não exista"""
        if not self.existe(): raise ValueError(f"{self} inexistente")
        return self.path.stat().st_size if not self.diretorio() else sum(
            caminho.path.stat().st_size if not self.diretorio() else caminho.tamanho
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

    def procurar (self, filtro: typing.Callable[[Caminho], SupportsBool], recursivo=False) -> list[Caminho]:
        """Procurar caminhos de acordo com o `filtro`
        - `recursivo` indicador para percorrer os diretórios filhos
        - Não tem efeito caso não seja diretório"""
        glob = self.path.rglob if recursivo else self.path.glob
        return [
            caminho
            for path in glob("*")
            if filtro(caminho := Caminho.from_path(path))
        ]

    def mimetype (self, fallback: str = "application/octet-stream") -> Mimetype:
        """Advinhar o mimetype do `Caminho` puramente pela extensão
        - `fallback` caso nenhum resultado"""
        tipo, _ = mimetypes.guess_type(self.string, strict=False)
        return Mimetype(tipo or fallback)

    # ------------------ #
    # Leitura de Arquivo #
    # ------------------ #

    def ler_texto (self) -> str:
        """Abrir o arquivo no modo texto, ler como `utf-8` e fechar o arquivo"""
        return self.path.read_text("utf-8", "ignore")

    def ler_bytes (self) -> bytes:
        """Abrir o arquivo no modo binário, ler e fechar o arquivo"""
        return self.path.read_bytes()

    # ---------------------------- #
    # Alteração no Nome do Caminho #
    # ---------------------------- #

    def com_nome (self, nome: str) -> Caminho:
        """Novo caminho com o `nome` alterado"""
        return Caminho.from_path(self.path.with_name(nome))

    def com_prefixo (self, prefixo: str) -> Caminho:
        """Novo caminho com o `prefixo` alterado"""
        return Caminho.from_path(self.path.with_stem(prefixo))

    def com_sufixo (self, sufixo: str) -> Caminho:
        """Novo caminho com o `sufixo` alterado"""
        sufixo = sufixo if sufixo.startswith(".") else f".{sufixo}"
        return Caminho.from_path(self.path.with_suffix(sufixo))

    # ---------------------- #
    # Modificação no Sistema #
    # ---------------------- #

    def renomear (self, novo_nome: str) -> Caminho:
        """Alterar o nome final do caminho para `novo_nome` e retornar o caminho destino
        - Sobrescreve os arquivos existentes (recursivamente se for diretório)
        - Não tem efeito caso caminho não exista"""
        destino = self.parente / novo_nome
        if self.arquivo():
            self.path.replace(destino.path)
        elif self.diretorio():
            shutil.copytree(self.path, destino.path, dirs_exist_ok=True)
            self.apagar_diretorio()
        return destino

    def copiar (self, diretorio: Caminho, prefixo: str | None = None) -> Caminho:
        """Copiar o arquivo ou diretório do caminho atual para o `diretorio` e retornar o caminho destino
        - `prefixo` para alterar o prefixo do destino.
        - Sobrescreve os arquivos existentes (recursivamente se for diretório)
        - Não tem efeito caso caminho não exista"""
        nome = self.nome if not prefixo else self.com_prefixo(prefixo).nome
        destino = diretorio.criar_diretorios() / nome
        if self.arquivo():
            shutil.copyfile(self.path, destino.path)
        elif self.diretorio():
            shutil.copytree(self.path, destino.path, dirs_exist_ok=True)
        return destino

    def mover (self, diretorio: Caminho) -> Caminho:
        """Mover o arquivo ou diretório do caminho atual para o `diretorio` e retornar o caminho
        - Sobrescreve os arquivos existentes (recursivamente se for diretório)
        - Não tem efeito caso caminho não exista"""
        destino = self.copiar(diretorio)
        self.apagar_diretorio() if self.diretorio() else self.apagar_arquivo()
        return destino

    def apagar_arquivo (self) -> Caminho:
        """Apagar o arquivo do caminho atual e retornar ao parente
        - Não tem efeito não seja arquivo"""
        if self.existe() and not self.diretorio():
            self.path.unlink()
        return self.parente

    def apagar_diretorio (self) -> Caminho:
        """Apagar o diretório e conteúdo do caminho atual e retornar ao parente
        - Não tem efeito caso não seja diretório"""
        if self.diretorio():
            for caminho in self:
                caminho.apagar_diretorio() if caminho.diretorio() else caminho.apagar_arquivo()
            self.path.rmdir()
        return self.parente

    def criar_diretorios (self) -> typing.Self:
        """Criar todos os diretórios no caminho atual que não existem
        - Não altera diretórios existentes"""
        if not self.existe(): self.path.mkdir(parents=True)
        return self

    def limpar_diretorio (self) -> typing.Self:
        """Limpar os arquivos e diretórios do diretório atual"""
        for filho in self:
            filho.apagar_diretorio() if filho.diretorio() else filho.apagar_arquivo()
        return self

__all__ = ["Caminho"]