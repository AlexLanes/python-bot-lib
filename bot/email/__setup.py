# std
from smtplib import SMTP
from typing import Generator
from imaplib import IMAP4_SSL
from email.message import Message
from re import search as re_search
from email import message_from_bytes
from email.mime.text import MIMEText
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import (
    datetime as Datetime, 
    timezone as TimeZone, 
    timedelta as TimeDelta
)
# interno
from .. import tipagem, logger, configfile, util, formatos, estruturas

def enviar_email (destinatarios: list[tipagem.email], assunto="", conteudo="", anexos: list[estruturas.Caminho] = []) -> None:
    """Enviar email para uma lista de `destinatarios` com `assunto`, `conteudo` e lista de `anexos`
    - Abstração `smtplib`
    - `conteudo` pode ser uma string html se começar com "<"
    - Variáveis .ini `[email.enviar] -> user, password, host`"""
    logger.informar(f"Enviando e-mail '{assunto}' para {str(destinatarios)}")
    assert destinatarios, "Pelo menos um e-mail é necessário para ser enviado"

    # variaveis do configfile
    user, password, host = configfile.obter_opcoes("email.enviar", ["user", "password", "host"])
    # from no-reply
    _from = f"no-reply <{user}>"

    mensagem = MIMEMultipart()
    # headers do e-mail
    mensagem["From"] = _from
    mensagem["To"] = ", ".join(destinatarios)
    mensagem["Subject"] = assunto
    # body do e-mail
    if conteudo and conteudo[0] == " ": # remover espaços vazios no começo
        conteudo = conteudo.lstrip()
    tipo = "html" if conteudo.startswith("<") else "plain" # html se começar com "<"
    mensagem.attach(MIMEText(conteudo, tipo))

    # anexos
    for caminho in anexos:
        if not caminho.arquivo():
            logger.alertar(f"Anexo para o e-mail não encontrado: {caminho}")
            continue
        with open(caminho.string, "rb") as arquivo:
            decodificar = any(formato in caminho.nome for formato in (".csv", ".txt", ".log"))
            conteudo = arquivo.read().decode(errors="ignore") if decodificar else arquivo.read()
            anexo = MIMEApplication(conteudo)
            nome = util.remover_acentuacao(caminho.nome)
            anexo.add_header("Content-Disposition", f'attachment; filename="{nome}"')
            mensagem.attach(anexo)

    # conectar ao servidor SMTP e enviar o e-mail
    try:
        with SMTP(host, 587) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            erro = smtp.sendmail(_from, destinatarios, mensagem.as_string())
            assert not erro, formatos.Json(erro).stringify(False)
    except Exception as erro:
        logger.alertar(f"Erro ao enviar e-mail\n\t{type(erro).__name__}\n\t{erro}")

def obter_emails (limite: int | slice = None, query="ALL", visualizar=False) -> Generator[estruturas.Email, None, None]:
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
    user, password, host = configfile.obter_opcoes("email.obter", ["user", "password", "host"])

    def extrair_email (email: str) -> tipagem.email:
        """Extrair apenas a parte do e-mail da string fornecida
        - `email` pode conter o nome da pessoa antes do email"""
        resultado = re_search(r"[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}", util.normalizar(email))
        if resultado == None:
            logger.alertar(f"Uma extração de e-mail não retornou resultado: '{email}'")
            return ""
        return resultado.group()
    def extrair_assunto (assunto: str) -> str:
        """Extrair assunto do e-mail e realizar o decode quando necessário
        - o subject pode vir em formatos não convencionais como `=?utf-8?B?Q29tbyBvIEhvbG1lcyByZWNlYmUgb3Mgbm92b3MgdXN1w6FyaW9z?=`"""
        decoded = [mensagem.decode(charset or "utf-8") if isinstance(mensagem, bytes) else mensagem 
                   for mensagem, charset in decode_header(assunto)]
        return "".join(decoded)
    def extrair_datetime (datetime: str | None) -> Datetime:
        """Extrair o datetime do e-mail e realizar o parse para o `Datetime` BRT
        - Retorna o Datetime.now() BRT caso seja None ou ocorra algum erro"""
        brt = TimeZone(TimeDelta(hours=-3))
        try:
            data: Datetime = parsedate_to_datetime(datetime)
            assert isinstance(data, Datetime)
            return data.astimezone(brt)
        except:
            logger.alertar(f"Extração do datetime '{datetime}' do email resultou em falha")
            return Datetime.now(brt)

    with IMAP4_SSL(host) as imap:
        imap.login(user, password)
        imap.select(readonly=not visualizar) # Selecionar Inbox e método de visualização

        # obter os ids da query
        uids: bytes = imap.search(None, query)[1][0] # ids em byte
        uids: list[str] = uids.decode().split(" ") # transformar para uma lista de ids em string
        uids = [*reversed(uids)][limite] # inverter para os mais recentes primeiro e aplicar o slice nos ids

        if not uids or uids[0] == "": return

        for uid in uids:
            email = estruturas.Email(int(uid), "", [], "", None, None, None, []) # armazenará as informações extraídas
            mensagem: bytes = imap.fetch(uid, '(RFC822)')[1][0][1] # bytes da mensagem
            mensagem: Message = message_from_bytes(mensagem) # parser email

            # marcar lido
            if visualizar: imap.store(uid, "+FLAGS", "SEEN")

            # extrair headers desejados
            email.remetente = extrair_email(mensagem.get("From", ""))
            email.destinatarios = [extrair_email(email) for email in mensagem.get("To", "").split(",")]
            email.assunto = extrair_assunto(mensagem.get("Subject", ""))
            email.data = extrair_datetime(mensagem.get("Date"))

            # navegar pelas partes do multipart/...
            # extrair o conteúdo e possíveis anexos
            for parte in mensagem.walk():
                # extrair anexo
                if "attachment" in parte.get("Content-Disposition", ""):
                    nome = parte.get_filename("blob")
                    tipo = parte.get_content_type()
                    arquivo = parte.get_payload(decode=True)
                    email.anexos.append((nome, tipo, arquivo))
                # extrai o conteúdo como string
                elif "text/plain" in parte.get_content_type():
                    payload: bytes = parte.get_payload(decode=True)
                    charset = parte.get_content_charset("utf-8")
                    email.texto = payload.decode(charset)
                # extrai o conteúdo html como string
                elif "text/html" in parte.get_content_type():
                    payload: bytes = parte.get_payload(decode=True)
                    charset = parte.get_content_charset("utf-8")
                    email.html = payload.decode(charset)

            yield email

__all__ = [
    "obter_emails",
    "enviar_email"
]
