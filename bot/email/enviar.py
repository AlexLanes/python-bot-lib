# std
import typing, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
# interno
import bot
from bot.estruturas import Caminho, String

def enviar_email (destinatarios: typing.Iterable[bot.tipagem.email],
                  assunto = "",
                  conteudo = "",
                  anexos: list[Caminho] = [],
                  no_reply: bool = True) -> None:
    """Enviar email para uma lista de `destinatarios` com `assunto`, `conteudo` e lista de `anexos`
    - Abstração `smtplib`
    - `conteudo` pode ser uma string html se começar com "<"
    - `no_reply` adicionar o `no-reply` no remetente
    - `anexos` do tipo `text` são enviados com o charset `utf-8`
    - Variáveis .ini `[email.enviar] -> user, password, host, [port: 587, ssl: False]`"""
    destinatarios = list[str](d for d in destinatarios)
    bot.logger.informar(f"Enviando e-mail '{assunto}' para {str(destinatarios)}")

    assert destinatarios, "Pelo menos um e-mail destinatário é necessário para ser enviado"

    # variaveis do configfile
    secao = "email.enviar"
    ssl = bot.configfile.obter_opcao_ou(secao, "ssl", False)
    port = bot.configfile.obter_opcao_ou(secao, "port", 587)
    user, password, host = bot.configfile.obter_opcoes_obrigatorias(secao, "user", "password", "host")

    # headers mensagem
    mensagem = MIMEMultipart()
    mensagem["From"] = (remetente := f"no-reply <{user}>" if no_reply else user)
    mensagem["To"] = ", ".join(destinatarios)
    mensagem["Subject"] = assunto
    # body mensagem
    # pode ser html
    if conteudo and conteudo[0] == " ": conteudo = conteudo.lstrip()
    tipo = "html" if conteudo.startswith("<") else "plain"
    mensagem.attach(MIMEText(conteudo, tipo))

    # anexos
    for caminho in anexos:
        if not caminho.arquivo():
            bot.logger.alertar(f"Anexo para o e-mail não encontrado", caminho=caminho)
            continue

        mimetype = caminho.mimetype()
        mensagem.attach(anexo := 
            MIMEText(caminho.ler_texto(), mimetype.subtipo, "utf-8")
            if mimetype.tipo == "text" else
            MIMEApplication(caminho.ler_bytes(), mimetype.subtipo)
        )
        anexo.add_header(
            "Content-Disposition",
            "attachment",
            filename = String(caminho.nome).remover_acentuacao()
        )

    # conectar ao servidor SMTP e enviar o e-mail
    try:
        TipoSMTP = smtplib.SMTP_SSL if ssl else smtplib.SMTP
        with TipoSMTP(host, port, timeout=10.0) as smtp:
            bot.estruturas.Resultado(smtp.starttls)
            smtp.login(user, password)
            erro = smtp.sendmail(remetente, destinatarios, mensagem.as_string())
            assert not erro, bot.formatos.Json(erro).stringify()
    except Exception as erro:
        bot.logger.alertar(f"Erro ao enviar e-mail")

__all__ = ["enviar_email"]