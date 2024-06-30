# std
import os, shutil, subprocess, itertools
# interno
from .. import tipagem, estruturas

# caminho para QRes no pacote do bot
CAMINHO_QRES = rf"{os.path.dirname(__file__)}\QRes.exe"

def apagar_arquivo (caminho: tipagem.caminho) -> None:
    """Apagar um arquivo"""
    if not caminho_existe(caminho): return
    assert afirmar_arquivo(caminho), f"O caminho '{caminho}' não é de um arquivo"
    os.remove(caminho)

def criar_pasta (caminho: tipagem.caminho) -> tipagem.caminho:
    """Criar pasta no `caminho` informado
    - Retorna o caminho absoluto da pasta criada"""
    os.mkdir(caminho)
    return caminho_absoluto(caminho)

def copiar_arquivo (de: tipagem.caminho, para: tipagem.caminho) -> tipagem.caminho:
    """Copiar arquivo `de` um caminho `para` outro
    - Retorna o caminho absoluto para o qual foi copiado"""
    return caminho_absoluto(shutil.copyfile(de, para))

def nome_base (caminho: tipagem.caminho) -> str:
    """Extrair a parte do nome e formato do `caminho`"""
    return os.path.basename(caminho)

def nome_diretorio (caminho: tipagem.caminho) -> str:
    """Extrair a parte do diretório do `caminho`"""
    disco, *caminho = os.path.dirname(caminho)
    chars = itertools.chain(disco.upper(), caminho)
    return "".join(chars)

def caminho_absoluto (caminho: tipagem.caminho) -> tipagem.caminho: 
    """Retorna a forma de caminho absoluto para o `caminho` informado"""
    disco, *caminho = os.path.abspath(caminho)
    chars = itertools.chain(disco.upper(), caminho)
    return "".join(chars)

def caminho_existe (caminho: tipagem.caminho) -> bool:
    """Confirmar se `caminho` existe ou não"""
    return os.path.exists(caminho)

def afirmar_pasta (caminho: tipagem.caminho) -> bool:
    """Confirmar se o `caminho` informado é de um diretório"""
    return os.path.isdir(caminho)

def afirmar_arquivo (caminho: tipagem.caminho) -> bool:
    """Confirmar se o `caminho` informado é de um arquivo"""
    return os.path.isfile(caminho)

def listar_diretorio (pasta: tipagem.caminho) -> estruturas.Diretorio:
    """Lista os caminhos dos arquivos e pastas do `caminhoPasta`"""
    assert caminho_existe(pasta), f"Caminho informado '{pasta}' não existe"
    assert afirmar_pasta(pasta), f"Caminho informado '{pasta}' não é de uma pasta"

    pasta = caminho_absoluto(pasta)
    diretorio = estruturas.Diretorio(pasta, [], [])
    for item in os.listdir(pasta):
        caminho = f"{pasta}\\{item}"
        if afirmar_pasta(caminho): diretorio.pastas.append(caminho)
        elif afirmar_arquivo(caminho): diretorio.arquivos.append(caminho)

    return diretorio

def diretorio_execucao () -> estruturas.Diretorio:
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
    return subprocess.check_output(comando, shell=True, timeout=timeout) \
                     .decode("utf-8", "ignore")

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
    "nome_diretorio",
    "copiar_arquivo",
    "afirmar_arquivo",
    "listar_diretorio",
    "caminho_absoluto",
    "alterar_resolucao",
    "diretorio_execucao",
    "informacoes_resolucao"
]
