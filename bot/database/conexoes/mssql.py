# externo
try: from sqlize.connections.mssql import MicrosoftSQL
except ImportError: raise ImportError(
    "Dependência opcional 'sqlize[mssql]' necessária. "
    "Instale como 'sqlize[mssql]' para utilizar o módulo 'bot.database.conexoes.mssql'"
) from None