# std
import typing, dataclasses, imaplib
from email.message import Message
from email import message_from_bytes
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import (
    datetime as Datetime, 
    timezone as TimeZone, 
    timedelta as TimeDelta
)
# interno
import bot
from bot.estruturas import String

@dataclasses.dataclass
class Email:
    """Classe para armazenar informações extraídas de Email"""

    uid: int
    """id do e-mail"""
    remetente: bot.tipagem.email
    """Remetente que enviou o e-mail"""
    destinatarios: list[bot.tipagem.email]
    """Destinatários que receberam o e-mail"""
    assunto: str
    """Assunto do e-mail"""
    data: Datetime
    """Data de envio do e-mail"""
    texto: str | None
    """Conteúdo do e-mail como texto"""
    html: str | None
    """Conteúdo do e-mail como html"""
    anexos: list[tuple[str, str, bytes]]
    """Anexos do e-mail
    - `for nome, tipo, conteudo in email.anexos:`"""

def extrair_email (email: str) -> bot.tipagem.email:
    """Extrair apenas a parte do e-mail da string fornecida
    - `email` pode conter o nome da pessoa antes do e-mail"""
    if resultado := String(email).re_search(r"[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}"):
        return resultado
    bot.logger.alertar(f"Uma extração de e-mail não retornou resultado", email=email)
    return ""

def extrair_assunto (assunto: str) -> str:
    """Extrair assunto do e-mail e realizar o decode quando necessário
    - O subject pode vir em formatos não convencionais como `=?utf-8?B?Q29tbyBvIEhvbG1lcyByZWNlYmUgb3Mgbm92b3MgdXN1w6FyaW9z?=`"""
    return "".join(
        mensagem.decode(charset or "utf-8") if isinstance(mensagem, bytes) else mensagem 
        for mensagem, charset in decode_header(assunto)
    )

def extrair_datetime (datetime: str | None) -> Datetime:
    """Extrair o datetime do e-mail e realizar o parse para o `Datetime` BRT
    - Retorna `Datetime.now()` BRT caso seja `None` ou ocorra algum erro"""
    brt = TimeZone(TimeDelta(hours=-3))
    try:
        data = parsedate_to_datetime(datetime)
        assert isinstance(data, Datetime)
        return data.astimezone(brt)
    except Exception:
        bot.logger.alertar(f"Extração do datetime '{datetime}' de e-mail resultou em falha")
        return Datetime.now(brt)

def obter_emails (limite: int | slice | None = None,
                  query = "ALL",
                  visualizar = False) -> typing.Generator[Email, None, None]:
    """Obter e-mails de uma `Inbox`
    - Abstração `imaplib`
    - Variáveis .ini `[email.obter] -> user, password, host`
    - `visualizar` Flag caso queria marcar o e-mail como a flag de visualizado
    - `query` pode variar de acordo com gmail e outlook. No outlook não é necessário as aspas simples em alguns casos
    - `query` search-criteria do fetch de acordo com documentação (https://www.marshallsoft.com/ImapSearch.htm)
        - ALL = Todos os emails
        - UNSEEN = Emails não vistos
        - FROM 'example@gmail.com' = Emails recebidos de
        - (OR (TO 'example@gmail.com') (FROM 'example@gmail.com')) = Emails enviados para OU recebidos de"""
    limite = limite if isinstance(limite, slice) else slice(limite)
    # variaveis do configfile
    user, password, host = bot.configfile.obter_opcoes_obrigatorias("email.obter", "user", "password", "host")

    with imaplib.IMAP4_SSL(host) as imap:
        imap.login(user, password)
        imap.select(readonly=not visualizar) # Selecionar Inbox e método de visualização

        # obter os ids da query
        uids_bytes: bytes = imap.search(None, query)[1][0] # type: ignore
         # inverter para os mais recentes primeiro e aplicar o slice nos ids
        uids = list(reversed(uids_bytes.decode().split(" ")))[limite]

        if not uids or uids[0] == "": return

        for uid in uids:
            # marcar lido
            if visualizar: imap.store(uid, "+FLAGS", "SEEN")

            # parse da mensagem
            bytes_email: bytes = imap.fetch(uid, '(RFC822)')[1][0][1] # type: ignore
            mensagem: Message = message_from_bytes(bytes_email)

            # criar estrutura
            email = Email(
                uid = int(uid),
                remetente = extrair_email(mensagem.get("From", "")),
                destinatarios = [extrair_email(email) for email in mensagem.get("To", "").split(",")],
                assunto = extrair_assunto(mensagem.get("Subject", "")),
                data = extrair_datetime(mensagem.get("Date")),
                texto = None,
                html = None,
                anexos = [],
            )

            # navegar pelas partes do multipart/...
            # extrair o conteúdo e possíveis anexos
            for parte in mensagem.walk():

                # extrair anexo
                if "attachment" in parte.get("Content-Disposition", ""):
                    nome = parte.get_filename("blob")
                    tipo = parte.get_content_type()
                    arquivo = parte.get_payload(decode=True)
                    email.anexos.append((nome, tipo, arquivo)) # type: ignore

                # extrai o conteúdo como string
                elif "text/plain" in parte.get_content_type():
                    payload: bytes = parte.get_payload(decode=True) # type: ignore
                    charset = parte.get_content_charset("utf-8")
                    email.texto = payload.decode(charset)

                # extrai o conteúdo html como string
                elif "text/html" in parte.get_content_type():
                    payload: bytes = parte.get_payload(decode=True) # type: ignore
                    charset = parte.get_content_charset("utf-8")
                    email.html = payload.decode(charset)

            yield email

__all__ = ["obter_emails"]