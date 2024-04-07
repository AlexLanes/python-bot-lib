# std
import os
import shutil
# interno
from bot.tipagem import caminho
from bot.estruturas import Diretorio


def apagar_arquivo (caminho: caminho) -> None:
    """Apagar um arquivo"""
    if not caminho_existe(caminho): return
    assert confirmar_arquivo(caminho), "O caminho informado não é de um arquivo"
    os.remove(caminho)


def criar_pasta (caminho: caminho) -> caminho:
    """Criar pasta no `caminho` informado
    - Retorna o caminho absoluto da pasta criada"""
    os.mkdir(caminho)
    return caminho_absoluto(caminho)


def copiar_arquivo (de: caminho, para: caminho) -> caminho:
    """Copiar arquivo `de` um caminho `para` outro
    - Retorna o caminho para o qual foi copiado"""
    return caminho_absoluto(shutil.copyfile(de, para))


def extrair_nome_base (caminho: caminho) -> str:
    """Extrair a parte do nome e formato do `caminho`"""
    return os.path.basename(caminho)


def caminho_absoluto (caminho: caminho) -> caminho: 
    """Retorna a forma de caminho absoluto para o `caminho` informado"""
    return os.path.abspath(caminho)


def caminho_existe (caminho: caminho) -> bool:
    """Confirmar se `caminho` existe ou não"""
    return os.path.exists(caminho)


def confirmar_pasta (caminho: caminho) -> bool:
    """Confirmar se o `caminho` informado é de um diretório"""
    return os.path.isdir(caminho)


def confirmar_arquivo (caminho: caminho) -> bool:
    """Confirmar se o `caminho` informado é de um arquivo"""
    return os.path.isfile(caminho)


def cmd (comando: str) -> None:
    """Realizar um comando no `prompt`
    - Levar em consideração o diretório de execução atual
    - Lança exceção se o comando for inválido"""
    os.system(comando)


def listar_diretorio (caminhoPasta: caminho) -> Diretorio:
    """Lista os caminhos dos arquivos e pastas do `caminhoPasta`"""
    assert caminho_existe(caminhoPasta), f"Caminho informado '{ caminhoPasta }' não existe"
    assert confirmar_pasta(caminhoPasta), f"Caminho informado '{ caminhoPasta }' não é de uma pasta"

    caminhoPasta = caminho_absoluto(caminhoPasta)
    diretorio = Diretorio(caminhoPasta, [], [])
    for item in os.listdir(caminhoPasta):
        caminho = f"{ caminhoPasta }\\{ item }"
        if confirmar_pasta(caminho): diretorio.pastas.append(caminho)
        elif confirmar_arquivo(caminho): diretorio.arquivos.append(caminho)

    return diretorio


def diretorio_execucao () -> Diretorio:
    """Obter informações do diretório de execução atual"""
    return listar_diretorio(os.getcwd())


__all__ = [
    "cmd",
    "criar_pasta",
    "caminho_existe",
    "apagar_arquivo",
    "copiar_arquivo",
    "confirmar_pasta",
    "listar_diretorio",
    "caminho_absoluto",
    "confirmar_arquivo",
    "extrair_nome_base",
    "diretorio_execucao"
]
