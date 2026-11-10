# std
import atexit, shutil
import os, tempfile, zipfile
from typing import Self
from datetime import datetime, timedelta
# interno
import bot
from bot.sistema import Caminho
# externo
import httpx

DIRETORIO_FFMPEG = Caminho.DiretorioUsuario() / "AppData" / "Local" / "bot-lib"
URL_FFMPEG = "https://github.com/AlexLanes/python-bot-lib/releases/download/ffmpeg-v1/ffmpeg-20261109-essentials_build.zip"

def checar_existencia_ffmpeg () -> bool:
    return shutil.which("ffmpeg") is not None

def baixar_ffmpeg (destino: Caminho) -> None:
    """Baixar o pacote do ffmpeg"""
    with httpx.stream("GET", URL_FFMPEG, follow_redirects=True, timeout=300) as response:
        response.raise_for_status()

        with open(destino.path, "wb") as writer:
            for bloco in response.iter_bytes(chunk_size=1024 * 1024):
                writer.write(bloco)

def instalar_ffmpeg () -> None:
    """Baixar e instalar o ffmpeg localmente"""
    DIRETORIO_FFMPEG.criar_diretorios()
    executavel = DIRETORIO_FFMPEG / "ffmpeg.exe"
    if executavel.existe():
        os.environ["PATH"] = os.pathsep.join((
            str(executavel.parente),
            os.environ['PATH']
        ))
        return

    print("FFmpeg: Baixando e extraindo o executável pelo GitHub")
    with tempfile.TemporaryDirectory() as tmp:
        diretorio = Caminho(tmp)
        arquivo = diretorio / URL_FFMPEG.split("/")[-1]

        baixar_ffmpeg(arquivo)
        with zipfile.ZipFile(arquivo.path) as pacote:
            pacote.extractall(DIRETORIO_FFMPEG.path)

    if not executavel.existe():
        raise FileNotFoundError("FFmpeg: Falha ao baixar e extrair o arquivo")

    os.environ["PATH"] = os.pathsep.join((
        str(executavel.parente),
        os.environ['PATH']
    ))
    if not checar_existencia_ffmpeg():
        raise RuntimeError("FFmpeg: Falha ao disponibilizar o executável no PATH após sua extração")

    print("FFmpeg: Baixado e adicionado ao PATH com sucesso", executavel)

class GravadorTela:
    """Classe para realizar a captura de vídeo da tela utilizando o `FFmpeg`.  
    O `FFmpeg` possui parâmetros customizáveis e é automaticamente instalado, de build no `GitHub`, caso não seja encontrado.  
    - `diretorio = ./logs_video` para configurar onde será salvo as gravações
    - Por padrão é gravado até um tempo limite de `1 hora`, que é customizável

    ## Exemplo
    ```
    gravador = GravadorTela()
    gravador.iniciar()                          # com nome automático
    gravador.iniciar(nome_extensao="xpto.mp4")  # com nome alterado
    caminho = gravador.parar() # parar a gravação e obter o caminho para o arquivo
    gravador.registrar_limpeza_diretorio()      # evitar o acúmulo de gravações no diretório

    # caso não queira obter o arquivo
    # o gravador continuará ativo até o encerramento do Python
    GravadorTela().registrar_limpeza_diretorio().iniciar()
    ```
    """

    diretorio: Caminho
    """Caminho para o diretório do arquivo
    - Default: `./logs_video`"""
    nome_extensao: str
    """nome do arquivo + extensão apropriada para o `vcodec`"""
    processo: bot.sistema.AbrirProcesso | None
    """Processo do ffmpeg"""

    # FFMPEG
    f: str = "gdigrab"
    """Formato de captura `Windows`"""
    i: str = "desktop"
    """Fonte de captura"""
    t: int = 60 * 60
    """Tempo máximo em segundos
    - Default `1 hora`"""
    framerate: int = 15
    """Quadros por segundo"""
    vcodec: str = "libx264"
    """Codec do vídeo
    - Determina o formato do vídeo
    - Default `mp4`"""
    preset: str = "ultrafast"
    """Nível de compressão
    - Default `ultrafast` | Arquivos maiores porém menos consumo de memória"""
    crf: int = 33
    """Fator de qualidade
    - `0`: sem perdas
    - `51`: pior qualidade
    - Default `33`"""

    def __init__ (self, diretorio: Caminho | None = None) -> None:
        if not checar_existencia_ffmpeg():
            bot.logger.informar("Biblioteca ffmpeg, utilizada para a gravação, não detectada")
            instalar_ffmpeg()

        self.processo = None
        self.diretorio = (diretorio or Caminho.DiretorioExecucao() / "logs_video").criar_diretorios()

    @property
    def argumentos (self) -> list[str]:
        """Argumentos para abrir o processo do `ffmpeg`
        - Usar apenas após `iniciar`"""
        return [
            "ffmpeg", "-y",
            "-f", self.f,
            "-framerate", str(self.framerate),
            "-i", self.i,
            "-vcodec", self.vcodec,
            "-preset", self.preset,
            "-crf", str(self.crf),
            "-t", str(self.t),
            str(self.diretorio / self.nome_extensao)
        ]

    @property
    def caminho (self) -> Caminho:
        """Caminho para o arquivo atual
        - Validado se o `caminho` existe
        - Usar apenas após `iniciar`"""
        caminho = self.diretorio / self.nome_extensao
        assert caminho.existe(), f"Caminho para o arquivo de vídeo não foi encontrado '{caminho}'"
        return caminho

    def iniciar (self, nome_extensao: str | None = None) -> Self:
        """Iniciar gravação e salvar com `nome_extensao` no `diretório`
        - Utilizado `data-hora.mp4` caso `nome_extensao=None`
        - Não iniciar uma nova gravação caso já exista uma em andamento
        - Registrado o `parar` automático ao fim do Python"""
        assert self.processo is None, "Não é possível iniciar duas gravações ao mesmo tempo"

        nome_extensao = nome_extensao or f"{datetime.now().strftime(r"%Y-%m-%dT%H-%M-%S")}.mp4"
        assert len(nome_extensao.split(".")) >= 2, f"Informe a extensão junto com o nome do arquivo: '{nome_extensao}'"
        self.nome_extensao = nome_extensao

        self.processo = bot.sistema.AbrirProcesso(*self.argumentos, shell=False)
        if self.processo.encerrado or not bot.tempo.aguardar(lambda: self.caminho.existe(), timeout=5, delay=0.25):
            try:
                returncode = self.processo.encerrar(timeout=10)
                stdout = self.processo.stdout()
                mensagem = f"Falha ao iniciar a gravação com ffmpeg, {returncode=} {stdout}"
            except Exception:
                mensagem = f"Falha ao iniciar a gravação com ffmpeg"
                bot.sistema.encerrar_processos_usuario("ffmpeg")
            bot.logger.erro(mensagem)
            raise Exception(mensagem)

        atexit.register(lambda: self.parar() if self.processo is not None else None)
        return self

    def parar (self) -> Caminho:
        """Parar a gravação e retornar o `Caminho`
        - Usar apenas após `iniciar`"""
        assert self.processo is not None, "Nenhuma gravação está em andamento para ser parada"

        stdout = b""
        try:
            if self.processo.executando:
                stdout = self.processo.comunicar(b"q", timeout=5)
            returncode = self.processo.returncode
            assert returncode == 0, f"Retorno do processo diferente do esperado: '{returncode}'"

        except Exception as erro:
            erro = Exception(f"Falha ao parar a gravação: {erro}")
            erro.add_note(stdout.decode(errors="ignore"))
            raise erro from None

        finally:
            p = self.processo
            self.processo = None
            p.encerrar()

        return self.caminho

    def registrar_limpeza_diretorio (self, *extensoes: str, limite_dias = 14) -> Self:
        """Registrar a execução da limpeza das gravações no `diretório` que ultrapassarem `limite_dias`
        - Execução realizada ao fim da execução do Python
        - `extensoes` informar as extensões que devem ser limpas. Default `.mp4`"""
        extensoes = tuple(map(str.lower, extensoes)) or (".mp4",)
        assert limite_dias >= 1, "Limite de dias para a limpeza do diretório dever ser >= 1"
    
        def limpar () -> None:
            agora = datetime.now()
            limite = timedelta(days=limite_dias)
            for caminho in self.diretorio:
                extensao = caminho.path.suffix.lower()
                if not caminho.arquivo(): continue
                if not any(extensao in e for e in extensoes): continue
                if (agora - caminho.data_modificao) < limite: continue
                caminho.apagar_arquivo()

        atexit.register(limpar)
        return self

__all__ = ["GravadorTela"]