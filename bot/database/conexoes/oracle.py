# externo
try: from sqlize.connections.oracle import Oracle
except ImportError: raise ImportError(
    "Dependência opcional 'sqlize[oracle]' necessária. "
    "Instale como 'sqlize[oracle]' para utilizar o módulo 'bot.database.conexoes.oracle'"
) from None