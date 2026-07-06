# externo
try: from sqlize.connections.odbc import ConnectionODBC
except ImportError: raise ImportError(
    "Dependência opcional 'sqlize[odbc]' necessária. "
    "Instale como 'sqlize[odbc]' para utilizar o módulo 'bot.database.conexoes.odbc'"
) from None