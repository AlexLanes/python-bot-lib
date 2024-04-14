# std
import os
import shutil
import subprocess
# interno
from bot.tipagem import caminho
from bot.estruturas import Diretorio


CAMINHO_QRES = r".\bot\windows\QRes.exe"


def apagar_arquivo (caminho: caminho) -> None:
    """Apagar um arquivo"""
    if not caminho_existe(caminho): return
    assert afirmar_arquivo(caminho), f"O caminho '{caminho}' não é de um arquivo"
    os.remove(caminho)


def criar_pasta (caminho: caminho) -> caminho:
    """Criar pasta no `caminho` informado
    - Retorna o caminho absoluto da pasta criada"""
    os.mkdir(caminho)
    return caminho_absoluto(caminho)


def copiar_arquivo (de: caminho, para: caminho) -> caminho:
    """Copiar arquivo `de` um caminho `para` outro
    - Retorna o caminho absoluto para o qual foi copiado"""
    return caminho_absoluto(shutil.copyfile(de, para))


def nome_base (caminho: caminho) -> str:
    """Extrair a parte do nome e formato do `caminho`"""
    return os.path.basename(caminho)


def caminho_absoluto (caminho: caminho) -> caminho: 
    """Retorna a forma de caminho absoluto para o `caminho` informado"""
    return os.path.abspath(caminho)


def caminho_existe (caminho: caminho) -> bool:
    """Confirmar se `caminho` existe ou não"""
    return os.path.exists(caminho)


def afirmar_pasta (caminho: caminho) -> bool:
    """Confirmar se o `caminho` informado é de um diretório"""
    return os.path.isdir(caminho)


def afirmar_arquivo (caminho: caminho) -> bool:
    """Confirmar se o `caminho` informado é de um arquivo"""
    return os.path.isfile(caminho)


def listar_diretorio (caminhoPasta: caminho) -> Diretorio:
    """Lista os caminhos dos arquivos e pastas do `caminhoPasta`"""
    assert caminho_existe(caminhoPasta), f"Caminho informado '{caminhoPasta}' não existe"
    assert afirmar_pasta(caminhoPasta), f"Caminho informado '{caminhoPasta}' não é de uma pasta"

    caminhoPasta = caminho_absoluto(caminhoPasta)
    diretorio = Diretorio(caminhoPasta, [], [])
    for item in os.listdir(caminhoPasta):
        caminho = f"{caminhoPasta}\\{item}"
        if afirmar_pasta(caminho): diretorio.pastas.append(caminho)
        elif afirmar_arquivo(caminho): diretorio.arquivos.append(caminho)

    return diretorio


def diretorio_execucao () -> Diretorio:
    """Obter informações do diretório de execução atual"""
    return listar_diretorio(os.getcwd())


def cmd (comando: str) -> None:
    """Realizar um `comando` no `prompt`
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    os.system(comando)


def powershell (comando: str, timeout: float | None = None) -> str:
    """Realizar um `comando` no `Windows PowerShell`
    - `stdout` do comando é retornado
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    return subprocess.check_output(comando, shell=True, timeout=timeout, encoding="utf-8")


def informacoes_resolucao () -> tuple[tuple[int, int], list[tuple[int, int]]]:
    """Obter informações sobre resolução da tela
    - `tuple[0]` Resolução atual da tela
    - `tuple[1]` Resoluções disponíveis"""
    resolucao_atual = tuple(map(int, 
        powershell(rf"{CAMINHO_QRES} /S").split("\n")[3].split(",")[0].split("x")
    ))

    resolucoes_unicas = sorted(
        tuple(map(int, resolucao.split("x")))
        for resolucao in { 
            linha_com_resolucao.split(",")[0]
            for linha_com_resolucao in powershell(rf"{CAMINHO_QRES} /L").split("\n")[3:-1]
        }
    )

    return (resolucao_atual, resolucoes_unicas)


def alterar_resolucao (largura: int, altura: int) -> None:
    """Alterar a resolução da tela
    - Utilizado o `QRes.exe` pois funciona para `RDPs`
    - A resolução deve estar presente nas disponíveis em configurações de tela do windows"""
    from bot.logger import informar, alertar
    informar(f"Alterando a resolução da tela para {largura}x{altura}")

    # checar
    desejada = (largura, altura)
    atual, disponiveis = informacoes_resolucao()
    if atual == desejada:
        return informar("Resolução da tela desejada já se encontra definida")
    if desejada not in disponiveis:
        return alertar("Resolução não disponível")

    # alterar
    sucesso = ['Mode Ok...']
    resultado = powershell(rf"{CAMINHO_QRES} /X:{largura} /Y:{altura}").split("\n")[3:-1]

    # confirmar
    if resultado == sucesso: informar(f"Resolução da tela alterada")
    else: alertar(f"Resolução da tela não foi alterada corretamente\n\t{resultado}")


__all__ = [
    "cmd",
    "nome_base",
    "powershell",
    "criar_pasta",
    "afirmar_pasta",
    "caminho_existe",
    "apagar_arquivo",
    "copiar_arquivo",
    "afirmar_arquivo",
    "listar_diretorio",
    "caminho_absoluto",
    "alterar_resolucao",
    "diretorio_execucao",
    "informacoes_resolucao"
]
