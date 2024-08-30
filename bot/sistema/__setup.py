# std
import subprocess
# interno
from ..estruturas import Caminho

# caminho para QRes no pacote do bot
CAMINHO_QRES = Caminho(__file__).parente / "QRes.exe"

def executar (*argumentos: str,
              powershell = False,
              timeout: float | None = None) -> tuple[bool, str]:
    """Executar um comando com os `argumentos` no `prompt` e aguarda finalizar
    - `powershell` para executar o comando no powershell ao invés do prompt
    - `timeout` define o tempo limite em segundos para `TimeoutError`
    - Retorno `(sucesso, mensagem)`"""
    argumentos = ("powershell", "-Command") + argumentos if powershell else argumentos
    try:
        resultado = subprocess.run(argumentos, capture_output=True, timeout=timeout)
        stdout = resultado.stdout.decode(errors="ignore").strip()
        stderr = resultado.stderr.decode(errors="ignore").strip()
        sucesso = stdout != ""
        return (sucesso, stdout if sucesso else stderr)
    except subprocess.TimeoutExpired as erro:
        raise TimeoutError() from erro
    except Exception as erro:
        return (False, str(erro))

def abrir_programa (*argumentos: str) -> None:
    """Abrir um programa em um novo processo descolado da `main thread`
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    subprocess.Popen(argumentos, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

    return (resolucao_atual, resolucoes_unicas)

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
    sucesso = "Mode Ok..."
    _, resultado = executar(CAMINHO_QRES.string, f"/X:{largura}", f"/Y:{altura}")

    # confirmar
    if sucesso in resultado: informar(f"Resolução da tela alterada")
    else: alertar(f"Resolução da tela não foi alterada corretamente\n\t{" ".join(resultado.split("\n")[3:])}")

__all__ = [
    "executar",
    "abrir_programa",
    "alterar_resolucao",
    "informacoes_resolucao"
]
