# std
import atexit, shutil, subprocess
from typing import Self
from datetime import datetime, timedelta
# interno
import bot
from bot.sistema import Caminho

def checar_existencia_ffmpeg () -> bool:
    return shutil.which("ffmpeg") is not None

@bot.util.decoradores.timeout(60)
def instalar_ffmpeg () -> None:
    if shutil.which("winget") is not None:
        bot.logger.informar("Realizando a instalação do ffmpeg via winget")
        sucesso, mensagem = bot.sistema.executar(
            "winget", "install", "ffmpeg",
            "--accept-source-agreements",
            "--accept-package-agreements",
            powershell = True,
        )
        if sucesso: return
        else: bot.logger.alertar(f"Falha ao instalar o ffmpeg via winget: {mensagem}")

    raise Exception("""Falha ao instalar o ffmpeg.
        \r\t- Caso não possua o gerenciador de pacotes 'winget' instalado, instale o 'chocolatey'
        \r\t- Abra o terminal como Admin, execute 'choco install ffmpeg-full' e confirme com 'y' caso requerido""")

class GravadorTela:
    """Classe para realizar a captura de vídeo da tela utilizando o `ffmpeg`.  
    O `ffmpeg` possui parâmetros customizáveis e é automaticamente instalado, via `winget`, caso não seja encontrado.  
    Caso não possua `winget`, será informado em erro para realizar a instalação manual do `ffmpeg` via `chocolatey`
    - `diretorio = ./video_logs` para configurar onde será salvo as gravações
    - `comprimir = True` Indicador para comprimir a gravação
    - Por padrão é gravado até um tempo limite de `1 hora`, que é customizável

    # Exemplo
    ```
    gravador = GravadorTela()
    gravador.iniciar()                          # com nome automático
    gravador.iniciar(nome_extensao="xpto.mp4")  # com nome alterado
    caminho = gravador.parar() # parar a gravação e obter o caminho para o arquivo
    gravador.registrar_limpeza_diretorio()      # evitar o acúmulo de gravações no diretório

    # caso não queira obter o arquivo
    # o gravador continuará ativo até o encerramento do Python
    GravadorTela().iniciar().registrar_limpeza_diretorio()
    ```
    """

    comprimir: bool
    """Indicador para comprimir a gravação para salvar espaço
    - Default: `True`"""
    diretorio: Caminho
    """Caminho para o diretório do arquivo
    - Default: `./video_logs`"""
    nome_extensao: str
    """nome do arquivo + extensão apropriada para o `vcodec`"""
    processo: subprocess.Popen[str] | None
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

    def __init__ (self, diretorio: Caminho | None = None, comprimir: bool = True) -> None:
        if not checar_existencia_ffmpeg():
            bot.logger.informar("Biblioteca ffmpeg, utilizada para a gravação, não detectada")
            instalar_ffmpeg()

        self.processo, self.comprimir = None, comprimir
        self.diretorio = (diretorio or Caminho.diretorio_execucao() / "video_logs").criar_diretorios()

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
    def argumentos_compressor (self) -> list[str]:
        """Argumentos para comprimir o vídeo via `ffmpeg`
        - Incluído `_comprimido` no nome do `destino`
        - Usar apenas após `parar`"""
        caminho = self.caminho
        destino = caminho.com_prefixo(f"{caminho.prefixo}_comprimido")
        return [
            "ffmpeg", "-y",
            "-i", caminho.string,
            "-vcodec", self.vcodec,
            "-preset", "veryfast",
            "-crf", str(self.crf),
            str(destino)
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

        self.processo = bot.sistema.abrir_processo(*self.argumentos)
        if self.processo.poll() is not None or not bot.util.aguardar_condicao(lambda: self.caminho.existe(), timeout=5):
            stdout, stderr = self.processo.communicate(timeout=3)
            mensagem = f"Falha ao iniciar a gravação com ffmpeg:\n{stdout}\n{stderr}"
            bot.logger.alertar(mensagem)
            raise Exception(mensagem)

        atexit.register(lambda: self.parar() if self.processo is not None else None)
        return self

    def parar (self) -> Caminho:
        """Parar a gravação e retornar o `Caminho`
        - Usar apenas após `iniciar`"""
        assert self.processo is not None, "Nenhuma gravação está em andamento para ser parada"

        try:
            if self.processo.poll() is None:
                self.processo.communicate("q", timeout=3)
            returncode = self.processo.poll()
            assert returncode == 0, f"Retorno do processo diferente do esperado: '{returncode}'"

        except Exception as erro:
            raise Exception(f"Falha ao parar a gravação: {erro}")

        finally:
            p = self.processo
            self.processo = None
            p.kill(); p.wait(1)

        if self.comprimir: self.__comprimir()
        return self.caminho

    def __comprimir (self) -> None:
        """Comprimir o `caminho` da gravação e substituir o original"""
        assert self.processo is None, "Não possível comprimir pois a gravação está em andamento"
        caminho = self.caminho

        try:
            argumentos = self.argumentos_compressor
            sucesso, mensagem = bot.sistema.executar(*argumentos, timeout=120)
            assert sucesso, mensagem
        except Exception as erro:
            raise Exception(f"Falha ao comprimir o arquivo da gravação {caminho!r}\n{erro}")

        Caminho(argumentos[-1]).renomear(caminho.nome)

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

__all__ = [
    "GravadorTela",
]