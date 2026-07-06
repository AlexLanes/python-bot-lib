# externo
try: from sqlize.connections.postgresql import PostgreSQL
except ImportError: raise ImportError(
    "Dependência opcional 'sqlize[postgresql]' necessária. "
    "Instale como 'sqlize[postgresql]' para utilizar o módulo 'bot.database.conexoes.postgresql'"
) from None