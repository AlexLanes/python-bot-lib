# std
import atexit, getpass, subprocess
# interno
from . import Caminho
import bot
# externo
import psutil
import win32event, win32api, win32clipboard # pywin32

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
    # checar
    desejada = (largura, altura)
    atual, _ = informacoes_resolucao()
    if atual == desejada:
        bot.logger.informar(f"Resolução da tela {desejada} já se encontra definida")
        return

    # alterar
    bot.logger.informar(f"Alterando a resolução da tela para {largura}x{altura}")
    _, resultado = executar(CAMINHO_QRES.string, f"/X:{largura}", f"/Y:{altura}")

    # confirmar
    sucesso = "Mode Ok..."
    if sucesso not in resultado: 
        erro = Exception(" ".join(resultado.split("\n")[3:]))
        bot.logger.erro(f"Resolução da tela {desejada} não foi aplicada corretamente", erro)
        raise erro

    bot.logger.informar(f"Resolução da tela alterada para {desejada}")

def copiar_texto (texto: str) -> None:
    """Substituir o texto copiado da área de transferência pelo `texto`"""
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(texto, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

def texto_copiado() -> str:
    """Obter o texto copiado da área de transferência"""
    win32clipboard.OpenClipboard()
    try: return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally: win32clipboard.CloseClipboard()

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

def criar_mutex (nome_mutex: str) -> bool:
    """Criar o mutex `nome_mutex` no sistema.  
    Impede a criação de outro mutex enquanto esse estiver ativo
    - Retornado se foi criado com sucesso
    - Útil para evitar duplicidade em execução
    - Mutex é segurado na memória até o fim da execução do Python"""
    ERRO_MUTEX_EXISTENTE = 183
    mutex = win32event.CreateMutex(None, False, nome_mutex) # type: ignore
    if win32api.GetLastError() == ERRO_MUTEX_EXISTENTE:
        return False

    atexit.register(lambda: mutex)
    return True

__all__ = [
    "executar",
    "criar_mutex",
    "copiar_texto",
    "texto_copiado",
    "abrir_processo",
    "alterar_resolucao",
    "informacoes_resolucao",
    "encerrar_processos_usuario"
]