# std
import ftplib
from typing import IO
from io import BytesIO
# interno
from .. import configfile, logger

class FTP:
    """Classe de abstração do `ftplib`"""

    __ftp: ftplib.FTP

    def __init__ (self) -> None:
        """Iniciar conexão com o FTP de acordo com as variáveis de ambiente .ini documentadas no módulo
        - Variáveis .ini `[FTP] -> host, user, password, timeout, port`
            - `host` Obrigatório
            - `user, password` Opcionais
            - `port` Opcional `Default: 21`
            - `timeout` Opcional `Default: 5.0`"""
        # instanciar e conectar
        self.__ftp = ftplib.FTP()
        host = configfile.obter_opcoes_obrigatorias("FTP", "host")[0]
        logger.informar(f"Conectando ao servidor FTP '{host}'")
        self.__ftp.connect(host=host,
                           port=configfile.obter_opcao_ou("FTP", "port", 21),
                           timeout=configfile.obter_opcao_ou("FTP", "timeout", 5.0))

        # login
        usuario, senha = configfile.obter_opcao_ou("FTP", "user"), configfile.obter_opcao_ou("FTP", "password")
        if usuario:
            logger.informar(f"Realizando o login com o usuário '{usuario}'")
            self.__ftp.login(usuario, senha)

    def __del__ (self, *args) -> None:
        """Encerrar conexão ao sair do escopo"""
        logger.informar("Encerrando conexão FTP")
        try: self.__ftp.quit()
        except: pass

    def __repr__ (self) -> str:
        return f"<FTP conexão com o host '{self.__ftp.host}'>"

    @property
    def diretorio (self) -> str:
        """Diretório atual do FTP"""
        return self.__ftp.pwd()

    def alterar_diretorio (self, caminho: str) -> None:
        """Alterar o diretório atual
        - Passível de exceção"""
        logger.informar(f"Alterando diretório do FTP para '{caminho}'")
        try: self.__ftp.cwd(caminho)
        except Exception as erro:
            erro.add_note(f"Caminho informado: '{caminho}'")
            erro.add_note(f"Caminhos existentes: {self.listar_diretorio()[1]}")
            raise

    def listar_diretorio (self) -> tuple[list[str], list[str]]:
        """Listar `arquivos, diretorios` existentes no diretório atual"""
        cwd = self.diretorio
        arquivos, diretorios = [], []

        for nome, infos in self.__ftp.mlsd():
            tipo, caminho = infos.get("type"), f"{cwd if cwd != "/" else ""}/{nome}"
            if tipo == "dir": diretorios.append(caminho)
            elif tipo == "file": arquivos.append(caminho)

        return arquivos, diretorios

    def obter_arquivo (self, nome_arquivo: str) -> bytes:
        """Obter conteúdo do arquivo `nome` no diretório atual
        - Passível de exceção"""
        logger.informar(f"Obtendo arquivo FTP '{nome_arquivo}'")
        conteudo = BytesIO()
        self.__ftp.retrbinary(f"RETR {nome_arquivo}", conteudo.write)
        return conteudo.getvalue()

    def adicionar_arquivo (self, nome_arquivo: str, conteudo: IO) -> None:
        """Adicionar arquivo no diretório atual
        - `conteudo` pode ser qualquer tipo do `import io` -> `open()`, inclusive `BytesIO`
        - Passível de exceção"""
        logger.informar(f"Adicionado arquivo FTP no diretório atual '{nome_arquivo}'")
        self.__ftp.storbinary(f"STOR {nome_arquivo}", conteudo)

    def renomear_arquivo (self, nome_atual: str, novo_nome: str) -> None:
        """Renomear arquivo no diretório atual
        - Pode ser utilizado para mover o arquivo também
        - Passível de exceção"""
        logger.informar(f"Renomeando arquivo FTP no diretório atual de '{nome_atual}' para '{novo_nome}'")
        self.__ftp.rename(nome_atual, novo_nome)

    def remover_arquivo (self, nome_arquivo: str) -> None:
        """Remover arquivo no diretório atual
        - Passível de exceção"""
        logger.informar(f"Removendo arquivo FTP no diretório atual '{nome_arquivo}'")
        self.__ftp.delete(nome_arquivo)

__all__ = ["FTP"]
