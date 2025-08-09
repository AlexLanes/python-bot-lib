# std
from __future__ import annotations
import os, subprocess
import typing, getpass
import shutil, pathlib
from datetime import datetime as Datetime
# externo
import pyperclip, psutil

class Caminho:
    """Classe para representação de caminhos, em sua versão absoluta, 
    do sistema operacional e manipulação de arquivos/diretórios

    - Criação: `Caminho("caminho_completo")`, `Caminho(".", "pasta", "arquivo.txt")` ou `Caminho.diretorio_execucao()`
    - Acesso: `Caminho().string` ou `str(Caminho())`
    - Concatenação: `Caminho() / "pasta" / "arquivo.txt"` ou `Caminho() + "pasta" + "arquivo.txt"`
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

    @classmethod
    def from_path (cls, path: pathlib.Path) -> Caminho:
        caminho = object.__new__(cls)
        caminho.path = path.resolve()
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

    def limpar_diretorio (self) -> typing.Self:
        """Limpar os arquivos e diretórios do diretório atual"""
        for filho in self:
            filho.apagar_diretorio() if filho.diretorio() else filho.apagar_arquivo()
        return self

    def procurar (self, filtro: typing.Callable[[Caminho], bool], recursivo=False) -> list[Caminho]:
        """Procurar caminhos de acordo com o `filtro`
        - `recursivo` indicador para percorrer os diretórios filhos
        - Não tem efeito caso não exista ou não seja diretório"""
        glob = self.path.rglob if recursivo else self.path.glob
        return [
            caminho
            for path in glob("*")
            if filtro(caminho := Caminho.from_path(path))
        ]

CAMINHO_QRES = Caminho(__file__).parente / "QRes.exe"

def executar (*argumentos: str,
              powershell = False,
              timeout: float | None = None) -> tuple[bool, str]:
    """Executar um comando com os `argumentos` no `prompt` e aguardar finalizar
    - `powershell` para executar o comando no powershell ao invés do prompt
    - `timeout` define o tempo limite em segundos para `TimeoutError`
    - Retorno `(sucesso, mensagem)`"""
    argumentos = ("powershell", "-Command") + argumentos if powershell else argumentos
    try:
        resultado = subprocess.run(argumentos, capture_output=True, timeout=timeout)
        stdout = resultado.stdout.decode(errors="ignore").strip()
        stderr = resultado.stderr.decode(errors="ignore").strip()
        sucesso = resultado.returncode == 0
        return (sucesso, stdout if sucesso else stderr)
    except subprocess.TimeoutExpired as erro:
        raise TimeoutError() from erro
    except Exception as erro:
        return (False, str(erro))

def abrir_processo (*argumentos: str, shell=False) -> subprocess.Popen[str]:
    """Abrir um processo descolado da `main thread`
    - Pode ser utilizado para abrir programas
    - Retornado classe `subprocess.Popen[str]` configurada
    - `stdin, stdout e stderr` são garantidos não serem `None` pois usam o `PIPE` e retornam `str` como `utf-8`"""
    return subprocess.Popen(
        argumentos,
        shell    = shell,
        stdin    = subprocess.PIPE,
        stdout   = subprocess.PIPE,
        stderr   = subprocess.PIPE,
        text     = True,
        encoding = "utf-8",
    )

def informacoes_resolucao () -> tuple[tuple[int, int], list[tuple[int, int]]]:
    """Obter informações sobre resolução da tela
    - `tuple[0]` Resolução atual da tela
    - `tuple[1]` Resoluções disponíveis"""
    resolucao_atual = tuple(
        int(pixel)
        for pixel in executar(CAMINHO_QRES.string, "/S")[1]
            .split("\n")[3]
            .split(",")[0]
            .split("x")
    )

    resolucoes_unicas = sorted(
        tuple(map(int, resolucao.split("x")))
        for resolucao in { 
            linha_com_resolucao.split(",")[0]
            for linha_com_resolucao in executar(CAMINHO_QRES.string, "/L")[1].split("\n")[3:]
        }
    )

    return (resolucao_atual, resolucoes_unicas) # type: ignore

def alterar_resolucao (largura: int, altura: int) -> None:
    """Alterar a resolução da tela
    - Utilizado o `QRes.exe` pois funciona para `RDPs`
    - A resolução deve estar presente nas disponíveis em configurações de tela do windows"""
    from bot.logger import informar, alertar

    # checar
    desejada = (largura, altura)
    atual, _ = informacoes_resolucao()
    if atual == desejada:
        return informar("Resolução da tela desejada já se encontra definida")

    # alterar
    informar(f"Alterando a resolução da tela para {largura}x{altura}")
    _, resultado = executar(CAMINHO_QRES.string, f"/X:{largura}", f"/Y:{altura}")

    # confirmar
    sucesso = "Mode Ok..."
    if sucesso in resultado: informar(f"Resolução da tela alterada")
    else: alertar(f"Resolução da tela não foi alterada corretamente\n\t{" ".join(resultado.split("\n")[3:])}")

def copiar_texto (texto: str) -> None:
    """Substituir o texto copiado da área de transferência pelo `texto`"""
    pyperclip.copy(texto)

def texto_copiado (apagar=False) -> str:
    """Obter o texto copiado da área de transferência
    - `apagar` determina se o texto será apagado após ser obtido"""
    texto = pyperclip.paste()
    if apagar: copiar_texto("")
    return texto

def encerrar_processos_usuario (*nome_processo: str) -> int:
    """Encerrar os processos do usuário atual que comecem com algum nome em `nome_processo`
    - `.exe` não necessário de ser informado
    - Retorna a quantidade de processos encerrados"""
    encerrados = 0
    atributos = ["name", "username"]
    usuario = getpass.getuser().lower()
    nome_processo = tuple(nome.lower() for nome in nome_processo)

    for processo in psutil.process_iter(atributos):
        name, username = (
            str(processo.info.get(attr, "")).lower()
            for attr in atributos
        )
        if not username.endswith(usuario): continue
        if not any(name.startswith(nome) for nome in nome_processo): continue

        processo.kill()
        processo.wait(5)
        encerrados += 1

    return encerrados

__all__ = [
    "Caminho",
    "executar",
    "copiar_texto",
    "texto_copiado",
    "abrir_processo",
    "alterar_resolucao",
    "informacoes_resolucao",
    "encerrar_processos_usuario"
]