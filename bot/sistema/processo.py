# std
from typing import Self
import subprocess, getpass, msvcrt
# externo
import psutil, win32pipe
from psutil import Process as P

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

def encerrar_processos_usuario (*nome_processo: str, timeout=5.0) -> list[str]:
    """Encerrar os processos do usuário atual que comecem com algum nome em `nome_processo`
    - `.exe` não necessário de ser informado
    - Retorna os nomes dos processos encerrados"""
    encerrados = list[str]()
    usuario = getpass.getuser().lower()
    nome_processo = tuple(nome.lower().strip() for nome in nome_processo)

    for processo in psutil.process_iter(atributos := ["name", "username"]):
        name, username = (
            str(processo.info.get(attr, "")).lower()
            for attr in atributos
        )
        if not username.endswith(usuario): continue
        if not any(name.startswith(nome) for nome in nome_processo): continue

        processo.kill()
        processo.wait(timeout)
        encerrados.append(name)

    return encerrados

class AbrirProcesso:
    """Abrir um processo descolado da `main thread`
    - Pode ser utilizado para abrir programas
    - Usar com o `with` para encerramento automático
    ### O processo pode abrir outro PID e fechar o aberto inicialmente"""

    nome: str
    caminho_executavel: str
    popen: subprocess.Popen[bytes]

    def __init__ (self, *argumentos: str, shell=False) -> None:
        self.popen = subprocess.Popen(
            argumentos,
            shell    = shell,
            stdin    = subprocess.PIPE,
            stdout   = subprocess.PIPE,
            stderr   = subprocess.STDOUT
        )
        p = P(self.popen.pid)
        self.nome = p.name()
        self.caminho_executavel = p.exe()

    def __repr__ (self) -> str:
        status = "executando" if self.executando else "encerrado"
        return f"<Processo pid={self.pid} nome={self.nome!r} status={status!r}>"

    def __enter__ (self) -> Self:
        return self

    def __exit__ (self, exc_type, exc, tb) -> None:
        if self.executando:
            self.encerrar()

    @property
    def pid (self) -> int:
        """`PID` do processo aberto"""
        return self.popen.pid

    @property
    def returncode (self) -> int | None:
        """`Returncode` de status do fim do processo
        - `None` caso não finalizado"""
        return self.popen.poll()

    @property
    def encerrado (self) -> bool:
        return self.popen.poll() is not None

    @property
    def executando (self) -> bool:
        return self.popen.poll() is None

    def stdout (self, encoding="utf-8", errors="ignore") -> str:
        """Ler o `stdout` disponível e realizar o decode
        - `encoding` `errors` usados no decode"""
        stdout = self.popen.stdout
        if stdout is None or not stdout.readable():
            return ""

        # peek
        try:
            handle = msvcrt.get_osfhandle(stdout.fileno())
            _, bytes_size, _ = win32pipe.PeekNamedPipe(handle, 0)
        except Exception:
            return ""

        # read
        if bytes_size == 0: return ""
        return stdout.read(bytes_size).decode(encoding=encoding, errors=errors)

    def encerrar (self, timeout: float | None = None) -> int:
        """Encerrar o `processo`, aguardar finalizar e obter o `returncode`
        - `timeout` lança `TimeoutError` caso ultrapasse o tempo"""
        self.popen.terminate()
        try: return self.popen.wait(timeout)
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"Processo {self.nome!r} não finalizou após {timeout} segundo(s), Argumentos{e.args[0]}") from None

    def comunicar (self, comando: bytes, timeout: float | None = None) -> bytes:
        """Encerrar o `processo` com o `comando`, aguardar finalizar e obter o `stdout`
        - `timeout` lança `TimeoutError` caso ultrapasse o tempo"""
        try: return self.popen.communicate(comando, timeout)[0]
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"Processo {self.nome!r} não finalizou após {timeout} segundo(s), Argumentos{e.args[0]}") from None

__all__ = [
    "executar",
    "AbrirProcesso",
    "encerrar_processos_usuario",
]