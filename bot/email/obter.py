# std
from typing import Self, Iterator
from datetime import date as Date, datetime as Datetime
# interno
import bot
# externo
import imap_tools

class Email:

    def __init__ (self, mail: imap_tools.MailMessage, client: imap_tools.MailBox) -> None:
        self.mail = mail
        self.__client = client

    def __repr__ (self) -> str:
        return f"<Email uid='{self.uid}' {self.assunto!r}>"

    @property
    def uid (self) -> str:
        """identificador do Email"""
        assert self.mail.uid, "UID do email é inválido"
        return self.mail.uid

    @property
    def data (self) -> Datetime:
        return self.mail.date.astimezone()

    @property
    def assunto (self) -> str:
        return self.mail.subject

    @property
    def remetente (self) -> bot.tipagem.email:
        return self.mail.from_

    @property
    def destinatarios (self) -> list[bot.tipagem.email]:
        return list(self.mail.to)

    def conteudo (self, html=False) -> str:
        """Obter o conteúdo do email
        - `html=True` para ler como html"""
        return self.mail.html if html else self.mail.text

    def anexos (self) -> list[imap_tools.MailAttachment]:
        """Anexos presentes no Email
        - `anexo.filename` nome do anexo
        - `anexo.content_type` mime type do anexo
        - `anexo.payload` para obter os `bytes`"""
        return self.mail.attachments

    def visualizar (self) -> Self:
        """Marcar como lido"""
        self.__client.flag(
            [self.uid],
            [imap_tools.MailMessageFlags.SEEN],
            True,
        )
        return self

    def copiar (self, pasta: str) -> Self:
        """Copiar o email para a `pasta`"""
        self.__client.copy(self.uid, pasta)
        return self

    def mover (self, pasta: str) -> Self:
        """Mover o email para a `pasta`"""
        self.__client.move(self.uid, pasta)
        return self

    def apagar (self) -> Self:
        """Apagar o email da pasta atual"""
        self.__client.delete(self.uid)
        return self

class CaixaEntradaIMAP:
    """Criar uma conexão IMAP para realizar a leitura / modificações em Emails
    - Abstração `imap_tools`
    - Variáveis .ini `[email.obter] -> [host: imap.gmail.com, port: 993, usuario, senha]`

    ## Inicialização, usado como contexto
    `with CaixaEntradaIMAP() as caixa: ...`
    ## Pastas
    - Inicialmente em `INBOX`
    - `caixa.pasta` nome da pasta atual
    - `caixa.pasta = "outra"` alterar pasta atual
    - `caixa.pastas()` pastas existentes
    ## Emails
    - `caixa.obter(...)` obter emails com critérios simplificados
    - `caixa.search(...)` obter emails com critério expandido
    """

    client: imap_tools.MailBox

    def __init__ (self, host: str = "imap.gmail.com",
                        port: int = 993,
                        *,
                        usuario: str | None = None,
                        senha: str | None = None) -> None:
        if "email_obter" in bot.config:
            secao = bot.config.email_obter
            usuario = usuario or secao.obter_ou("usuario")
            senha = senha or secao.obter_ou("senha")
            host = secao.obter_ou("host", host)
            port = secao.obter_ou("port", port)

        self.__pasta = "INBOX"
        assert usuario and senha, "Necessário informar `CaixaEntradaIMAP(usuario=, senha=)` via argumentos ou configfile"
        try: self.client = imap_tools.MailBox(host=host, port=port, timeout=3)\
                                     .login_utf8(username=usuario, password=senha, initial_folder=self.__pasta)
        except Exception as erro:
            raise Exception(f"Falha Conexão/Login IMAP `{usuario}` -> `{host}:{port}` | {erro}")

    def __enter__ (self) -> Self:
        return self

    def __exit__ (self, exc_type, exc, tb) -> None:
        self.client.__exit__(exc_type, exc, tb)

    def __repr__ (self) -> str:
        return f"<CaixaEntradaIMAP {self.pasta!r}>"

    @property
    def pasta (self) -> str:
        """Nome da pasta atualmente selecionada
        - Use `self.pasta = ""` para alterar"""
        return self.__pasta

    @pasta.setter
    def pasta (self, nome: str) -> None:
        if nome == self.__pasta:
            return
        try:
            self.client.folder.set(nome)
            self.__pasta = nome
        except Exception as erro:
            raise Exception(f"Falha ao alterar a pasta IMAP para {nome!r} | {erro}")

    def pastas (self) -> list[str]:
        """Nome das pastas existentes"""
        self.client.fetch()
        return [
            folder.name
            for folder in self.client.folder.list()
        ]

    def obter (self, limite: int = 100,
                     *,
                     mais_recentes: bool = False,
                     visualizado: bool | None = None,
                     remetente: str | None = None,
                     destinatario: str | None = None,
                     assunto: str | None = None,
                     desde: Date | None = None,
                     antes_de: Date | None = None) -> Iterator[Email]:
        """Obter emails de acordo com os critérios nomeados
        - `mais_recentes=True` Mais recentes primeiro
        - `visualizado` Filtrar apenas os que foram visualizados ou não"""
        criterios = {}

        if visualizado is True: criterios["seen"] = True
        elif visualizado is False: criterios["seen"] = False

        if remetente: criterios["from_"] = remetente
        if destinatario: criterios["to"] = destinatario
        if assunto: criterios["subject"] = assunto
        if desde is not None: criterios["date_gte"] = desde
        if antes_de is not None: criterios["date_lt"] = antes_de

        return self.search(
            query = imap_tools.AND(**criterios).combine_params()
                    if criterios
                    else "ALL",
            limite = limite,
            mais_recentes = mais_recentes,
        )

    def search (self, query: str = "ALL",
                      limite: int = 100,
                      *,
                      mais_recentes: bool = False) -> Iterator[Email]:
        """Obter emails de acordo com a `query` aceita pelo IMAP
        - `mais_recentes=True` Mais recentes primeiro
        - Referência: https://www.marshallsoft.com/ImapSearch.htm"""
        for mail in self.client.fetch(query, "UTF-8",
                                      limit = limite,
                                      reverse = mais_recentes,
                                      mark_seen = False):
            yield Email(mail, self.client)

__all__ = ["CaixaEntradaIMAP"]