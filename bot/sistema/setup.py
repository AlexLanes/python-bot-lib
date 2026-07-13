# std
import atexit
# interno
from . import Caminho, executar
# externo [pywin32]
import win32event, win32api, win32clipboard

CAMINHO_QRES = Caminho(__file__).parente / "QRes.exe"

class Resolucao:
    """Obter informações e realizar modificações da resolução da tela
    - Utilizado o `QRes.exe` pois funciona para `RDPs`
    - Possível de realizar comparação `==` com os valores `(largura, altura)` `f"{largura}x{altura}"`"""

    atual: tuple[int, int]

    def __init__ (self) -> None:
        largura, altura = tuple(
            int(pixel)
            for pixel in executar(CAMINHO_QRES.string, "/S")[1]
                .split("\n")[3]
                .split(",")[0]
                .split("x")
        )
        self.atual = (largura, altura)

    def __repr__ (self) -> str:
        return f"<Resolução {self.atual[0]}x{self.atual[1]}>"

    def __eq__ (self, value: object) -> bool:
        a = self.atual
        match value:
            case str(): return f"{a[0]}x{a[1]}" == value.replace(" ", "").strip()
            case (int(), int()): return a == value
            case _: return NotImplemented

    @property
    def disponiveis (self) -> list[tuple[int, int]]:
        linhas_com_resolucao = executar(CAMINHO_QRES.string, "/L")[1].split("\n")[3:]
        return sorted(
            (int(largura), int(altura))
            for largura, altura in { 
                tuple(linha.split(",")[0].split("x"))
                for linha in linhas_com_resolucao
            }
        )

    def alterar (self, largura: int, altura: int) -> None:
        desejada = (largura, altura)
        if self == desejada: return

        _, mensagem = executar(CAMINHO_QRES.string, f"/X:{largura}", f"/Y:{altura}", timeout=10)
        if "Mode Ok..." in mensagem:
            self.atual = desejada
            return

        mensagem = " ".join(mensagem.split("\n")[3:]).removeprefix("Error:").strip()
        erro = Exception(f"Falha ao alterar para a resolução {desejada} | {mensagem}")
        raise erro

def copiar_texto (texto: str) -> None:
    """Substituir o texto copiado da área de transferência pelo `texto`"""
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(texto, win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

def texto_copiado () -> str:
    """Obter o texto copiado da área de transferência"""
    win32clipboard.OpenClipboard()
    try: return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally: win32clipboard.CloseClipboard()

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
    "Resolucao",
    "criar_mutex",
    "copiar_texto",
    "texto_copiado",
]