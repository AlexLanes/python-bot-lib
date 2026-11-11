# std
import tempfile
# interno
import bot
from bot.sistema import Caminho

DIRETORIO_INSPECT = Caminho.DiretorioUsuario() / "AppData" / "Local" / "bot-lib"
URL_INSPECT = "https://github.com/AlexLanes/python-bot-lib/releases/download/inspect-v1/inspect.zip"

def instalar_inspect () -> Caminho:
    """Baixar e instalar o inspect localmente"""
    DIRETORIO_INSPECT.criar_diretorios()
    executavel = DIRETORIO_INSPECT / "inspect.exe"
    if executavel.existe():
        return executavel

    print("Inspect.exe: Baixando e extraindo o executável pelo GitHub")
    with tempfile.TemporaryDirectory() as tmp:
        bot.http.download(URL_INSPECT, Caminho(tmp))\
                .descompactar(DIRETORIO_INSPECT)

    if not executavel.existe():
        raise FileNotFoundError("Inspect.exe: Falha ao baixar e extrair o arquivo")

    print("Inspect.exe: Baixado e adicionado ao PATH com sucesso", executavel)
    return executavel

def executar () -> None:
    instalar_inspect()
    bot.sistema.AbrirProcesso(str(DIRETORIO_INSPECT / "inspect.exe"), shell=True)
