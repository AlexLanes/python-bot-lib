
# std
import ftplib
from io import BytesIO
from typing import Self
# interno
import bot
import bot.configfile as cf


class FTP:
    """Classe de abstração do `ftplib`
    - Utilizar com contexto `with FTP() as ftp`"""
    __ftp: ftplib.FTP
    
    def __enter__ (self) -> Self:
        # instanciar e conectar
        self.__ftp = ftplib.FTP()
        host = cf.obter_opcoes("FTP", ["host"])[0]
        bot.logger.informar(f"Conectando ao servidor FTP '{ host }'")
        self.__ftp.connect(host=host,
                           port=int(cf.obter_opcao("FTP", "port", "21")),
                           timeout=int(cf.obter_opcao("FTP", "timeout", "5")))
        # login
        usuario, senha = cf.obter_opcao("FTP", "user"), cf.obter_opcao("FTP", "password")
        if usuario:
            bot.logger.informar(f"Realizando o login com o usuário '{ usuario }'")
            self.__ftp.login(usuario, senha)

        return self
    
    def __exit__ (self, *args) -> None:
        bot.logger.informar("Encerrando conexão FTP")
        self.__ftp.quit()
    
    def __repr__ (self) -> str:
        return f"<FTP conexão com o host '{ self.__ftp.host }'>"

    def alterar_diretorio (self, caminho: bot.tipagem.caminho) -> None:
        """Alterar o diretório atual
        - Passível de exceção"""
        try: self.__ftp.cwd(caminho)
        except Exception as erro:
            erro.add_note(f"Caminho informado: '{ caminho }'")
            erro.add_note(f"Caminhos existentes: { self.listar_diretorio().pastas }")
            raise

    def listar_diretorio (self) -> bot.tipagem.Diretorio:
        """Listar arquivos e pastas do diretório atual"""
        cwd = self.__ftp.pwd()
        diretorio = bot.tipagem.Diretorio(cwd, [], [])
        
        for nome, infos in self.__ftp.mlsd():
            tipo, caminho = infos.get("type"), f"{ cwd if cwd != '/' else '' }/{ nome }"
            if tipo == "dir": diretorio.pastas.append(caminho)
            elif tipo == "file": diretorio.arquivos.append(caminho)

        return diretorio

    def obter_arquivo (self, nome: str) -> bytes:
        """Obter conteúdo do arquivo `nome` no diretório atual
        - Passível de exceção"""
        conteudo = BytesIO()
        self.__ftp.retrbinary(f"RETR { nome }", conteudo.write)
        return conteudo.getvalue()


__all__ = ["FTP"]
