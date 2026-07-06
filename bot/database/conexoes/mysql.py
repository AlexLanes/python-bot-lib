# externo
try: from sqlize.connections.mysql import MySQL
except ImportError: raise ImportError(
    "Dependência opcional 'sqlize[mysql]' necessária. "
    "Instale como 'sqlize[mysql]' para utilizar o módulo 'bot.database.conexoes.mysql'"
) from None