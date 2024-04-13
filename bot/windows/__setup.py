# std
import os
import shutil
import win32con
# interno
from bot.tipagem import caminho
from bot.estruturas import Diretorio
# externo
import win32api


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


def cmd (comando: str) -> None:
    """Realizar um comando no `prompt`
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    os.system(comando)


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


def resolucao_tela () -> tuple[int, int]:
    """Obter a resolução da tela atual"""
    nome_tela = win32api.EnumDisplayDevices(None, 0).DeviceName
    configuracoes = win32api.EnumDisplaySettings(nome_tela, win32con.ENUM_CURRENT_SETTINGS)
    return (configuracoes.PelsWidth, configuracoes.PelsHeight)


def alterar_resolucao (largura: int, altura: int) -> None:
    """Alterar a resolução da tela
    - A resolução deve estar presente nas resoluções aceitadas pelas configurações da tela"""
    from bot.logger import informar, alertar
    informar(f"Alterando a resolução da tela para {largura}x{altura}")
    if resolucao_tela() == (largura, altura):
        return informar("Resolução da tela desejada já definida")

    # configura a nova resolução
    nome_tela = win32api.EnumDisplayDevices(None, 0).DeviceName
    configuracoes = win32api.EnumDisplaySettings(nome_tela, win32con.ENUM_CURRENT_SETTINGS)
    configuracoes.PelsWidth = largura
    configuracoes.PelsHeight = altura
    configuracoes.Fields = configuracoes.Fields | win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT

    # alterar
    win32api.ChangeDisplaySettingsEx(nome_tela, configuracoes)

    # confirmar
    configuracoes = win32api.EnumDisplaySettings(nome_tela, win32con.ENUM_CURRENT_SETTINGS)
    if (configuracoes.PelsWidth, configuracoes.PelsHeight) == (largura, altura):
        informar(f"Resolução da tela alterada")
    else: alertar("Resolução da tela não foi alterada")


__all__ = [
    "cmd",
    "nome_base",
    "criar_pasta",
    "afirmar_pasta",
    "caminho_existe",
    "apagar_arquivo",
    "copiar_arquivo",
    "resolucao_tela",
    "afirmar_arquivo",
    "listar_diretorio",
    "caminho_absoluto",
    "alterar_resolucao",
    "diretorio_execucao"
]
