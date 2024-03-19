
# std
import ftplib
from typing import IO
from io import BytesIO
# interno
import bot
import bot.configfile as cf


class FTP:
    """Classe de abstração do `ftplib`"""
    __ftp: ftplib.FTP
    
    def __init__ (self) -> None:
        """Iniciar conexão com o FTP de acordo com as variáveis de ambiente .ini documentadas no módulo"""
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
    
    def __del__ (self, *args) -> None:
        """Encerrar conexão ao sair do escopo"""
        bot.logger.informar("Encerrando conexão FTP")
        self.__ftp.quit()
    
    def __repr__ (self) -> str:
        return f"<FTP conexão com o host '{ self.__ftp.host }'>"

    @property
    def diretorio (self) -> str:
        """Diretório atual do FTP"""
        return self.__ftp.pwd()

    def alterar_diretorio (self, caminho: bot.tipagem.caminho) -> None:
        """Alterar o diretório atual
        - Passível de exceção"""
        bot.logger.informar(f"Alterando diretório do FTP para '{ caminho }'")
        try: self.__ftp.cwd(caminho)
        except Exception as erro:
            erro.add_note(f"Caminho informado: '{ caminho }'")
            erro.add_note(f"Caminhos existentes: { self.listar_diretorio().pastas }")
            raise

    def listar_diretorio (self) -> bot.tipagem.Diretorio:
        """Listar arquivos e pastas do diretório atual"""
        cwd = self.diretorio
        diretorio = bot.tipagem.Diretorio(cwd, [], [])
        
        for nome, infos in self.__ftp.mlsd():
            tipo, caminho = infos.get("type"), f"{ cwd if cwd != '/' else '' }/{ nome }"
            if tipo == "dir": diretorio.pastas.append(caminho)
            elif tipo == "file": diretorio.arquivos.append(caminho)

        return diretorio

    def obter_arquivo (self, nome_arquivo: str) -> bytes:
        """Obter conteúdo do arquivo `nome` no diretório atual
        - Passível de exceção"""
        bot.logger.informar(f"Obtendo arquivo FTP '{ nome_arquivo }'")
        conteudo = BytesIO()
        self.__ftp.retrbinary(f"RETR { nome_arquivo }", conteudo.write)
        return conteudo.getvalue()
    
    def adicionar_arquivo (self, nome_arquivo: str, conteudo: IO) -> None:
        """Adicionar arquivo no diretório atual
        - `conteudo` pode ser qualquer tipo do `import io` -> `open()`, inclusive `BytesIO`
        - Passível de exceção"""
        bot.logger.informar(f"Adicionado arquivo FTP no diretório atual '{ nome_arquivo }'")
        self.__ftp.storbinary(f"STOR { nome_arquivo }", conteudo)
    
    def renomear_arquivo (self, nome_atual: str, novo_nome: str) -> None:
        """Renomear arquivo no diretório atual
        - Pode ser utilizado para mover o arquivo também
        - Passível de exceção"""
        bot.logger.informar(f"Renomeando arquivo FTP no diretório atual de '{ nome_atual }' para '{ novo_nome }'")
        self.__ftp.rename(nome_atual, novo_nome)

    def remover_arquivo (self, nome_arquivo: str) -> None:
        """Remover arquivo no diretório atual
        - Passível de exceção"""
        bot.logger.informar(f"Removendo arquivo FTP no diretório atual '{ nome_arquivo }'")
        self.__ftp.delete(nome_arquivo)


__all__ = ["FTP"]
