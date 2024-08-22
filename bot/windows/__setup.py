# std
import os, shutil, subprocess, itertools
# interno
from .. import tipagem, estruturas

# caminho para QRes no pacote do bot
CAMINHO_QRES = os.path.join(os.path.dirname(__file__), "QRes.exe")

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

def renomear_arquivo (arquivo: tipagem.caminho, nome: str) -> tipagem.caminho:
    """Renomear o `arquivo` para o novo `nome` + `.formato`
    - Retorna o caminho para o novo nome"""
    assert afirmar_arquivo(arquivo), f"Caminho informado {arquivo} não é de um arquivo"
    nome = caminho_absoluto(os.path.join(nome_diretorio(arquivo), nome))
    os.rename(arquivo, nome)
    return nome

def nome_base (caminho: tipagem.caminho) -> str:
    """Extrair a parte final do `nome.formato` ou `nome pasta` do `caminho`"""
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

def afirmar_diretorio (caminho: tipagem.caminho) -> bool:
    """Confirmar se o `caminho` informado é de um diretório"""
    return os.path.isdir(caminho)

def afirmar_arquivo (caminho: tipagem.caminho) -> bool:
    """Confirmar se o `caminho` informado é de um arquivo"""
    return os.path.isfile(caminho)

def listar_diretorio (caminho: tipagem.caminho) -> estruturas.Diretorio:
    """Lista os caminhos dos arquivos e pastas do `caminho`"""
    assert caminho_existe(caminho), f"Caminho informado '{caminho}' não existe"
    assert afirmar_diretorio(caminho), f"Caminho informado '{caminho}' não é de um diretório"

    diretorio = estruturas.Diretorio(caminho_absoluto(caminho), [], [])
    for item in os.listdir(caminho):
        caminho = os.path.join(diretorio.caminho, item)
        if afirmar_diretorio(caminho): diretorio.pastas.append(caminho)
        elif afirmar_arquivo(caminho): diretorio.arquivos.append(caminho)

    return diretorio

def diretorio_execucao () -> estruturas.Diretorio:
    """Obter informações do diretório de execução atual"""
    return listar_diretorio(os.getcwd())

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
        for pixel in executar(CAMINHO_QRES, "/S")[1]
            .split("\n")[3]
            .split(",")[0]
            .split("x")
    )

    resolucoes_unicas = sorted(
        tuple(map(int, resolucao.split("x")))
        for resolucao in { 
            linha_com_resolucao.split(",")[0]
            for linha_com_resolucao in executar(CAMINHO_QRES, "/L")[1].split("\n")[3:]
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
    _, resultado = executar(CAMINHO_QRES, f"/X:{largura}", f"/Y:{altura}")

    # confirmar
    if sucesso in resultado: informar(f"Resolução da tela alterada")
    else: alertar(f"Resolução da tela não foi alterada corretamente\n\t{" ".join(resultado.split("\n")[3:])}")

__all__ = [
    "executar",
    "nome_base",
    "criar_pasta",
    "caminho_existe",
    "apagar_arquivo",
    "nome_diretorio",
    "copiar_arquivo",
    "abrir_programa",
    "afirmar_arquivo",
    "renomear_arquivo",
    "listar_diretorio",
    "caminho_absoluto",
    "afirmar_diretorio",
    "alterar_resolucao",
    "diretorio_execucao",
    "informacoes_resolucao"
]
