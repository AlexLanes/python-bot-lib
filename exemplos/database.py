import bot
from bot.database.setup import ResultadoSQL

"""Pacote polars, utilizado para criar Dataframes ou ler arquivos tabulados"""
df = bot.database.polars.read_csv("caminho")
df = bot.database.polars.DataFrame({ "a": [1, 2], "b": ["a", "b"] })
"""
shape: (2, 2)
┌─────┬─────┐
│ a   ┆ b   │
│ --- ┆ --- │
│ i64 ┆ str │
╞═════╪═════╡
│ 1   ┆ a   │
│ 2   ┆ b   │
└─────┴─────┘
"""


"""Criar um arquivo excel com os dados do Dataframe"""
caminho_destino = bot.database.criar_excel(
    bot.estruturas.Caminho("dados.xlsx"),
    { "planilha1": df }
)


"""
Classe ResultadoSQL
Utilizada no retorno para instruções em banco de dados
Não necessário instanciar a classe pois será retornada pelos métodos `execute` e `execute_many`
"""
resultado = ResultadoSQL() # type: ignore
resultado.linhas_afetadas # Linhas afetadas pelo comando SQL (se houver)
resultado.colunas # Colunas das linhas retornadas (se houver)
resultado.linhas # Generator das linhas retornadas (se houver)
len(resultado) # Obter a quantidade de linhas no retornadas
resultado["coluna"] # Obter o valor da coluna na primeira linha
resultado.to_dataframe() # Salvar as colunas e linhas do resultado em um `polars.DataFrame`
# Iteração sobre as linhas
for linha in resultado: ...
for linha in resultado.linhas: ...
# Checar se o resultado teve linhas_afetadas ou linhas retornadas
bool(resultado)
if resultado: ...



"""
Classe destinada para conexão com banco de dados sqlite3
"""
# Abrindo conexão
db = bot.database.Sqlite() # Aberto na memória
db = bot.database.Sqlite("caminho.sqlite") # Aberto como arquivo
# Métodos úteis
db.tabelas() # Nome das tabelas existentes
db.colunas("tabela") # Nome e tipo das colunas da tabela informada
db.commit() # Commitar alterações feitas na conexão
db.rollback() # Reverter as alterações, pós commit, feitas na conexão
db.to_excel(bot.estruturas.Caminho("dados.xlsx")) # Salvar as linhas de todas as tabelas da conexão no `caminho` formato excel
# Executar uma única instrução SQL
# Veja como utilizar `ResultadoSQL`
db.execute("select * from tabela") # Sem parâmetro
db.execute("select * from tabela where nome = ?", "Alex") # Com parâmetro posicional '?'
db.execute("select * from tabela where nome = :nome", nome="Alex") # Com parâmetro nomeado ':'
# Executar uma ou mais instruções SQL
# Veja como utilizar `ResultadoSQL`
db.execute_many("insert into tabela values (?, ?)", [("Alex", 11), ("Fulano", 22)]) # (2 execuções) com parâmetros posicionais '?'
db.execute_many("insert into tabela values (:nome, :codigo)", [{"nome": "Alex", "codigo": 11}]) # (1 execução) com parâmetros nomeados ':'



"""
class DatabaseODBC
Classe para manipulação de Databases via drivers ODBC
Necessário possuir o driver instalado em `ODBC Data Sources`
"""
# Abrindo conexão
db = bot.database.DatabaseODBC(
    "PostgreSQL Unicode(x64)",
    uid = "usuário",
    pwd = "senha",
    server = "servidor",
    port = "porta",
    database = "nome do database",
)
# Métodos úteis
bot.database.DatabaseODBC.listar_drivers() # Nome dos drivers disponíveis
db.tabelas() # Nomes das tabelas e schemas disponíveis
db.colunas("tabela") # Nomes das colunas e tipos da tabela
db.commit() # Commitar alterações feitas na conexão
db.rollback() # Reverter as alterações, pós commit, feitas na conexão
db.reconectar() # Refaz a conexão caso encerrada
# Executar uma única instrução SQL
# Veja como utilizar `ResultadoSQL`
db.execute("select * from tabela") # Sem parâmetro
db.execute("select * from tabela where nome = ?", "Alex") # Com parâmetro posicional '?'
# Executar uma ou mais instruções SQL
# Veja como utilizar `ResultadoSQL`
db.execute_many("insert into tabela values (?, ?)", [("Alex", 11), ("Fulano", 22)]) # (2 execuções) com parâmetros posicionais '?'
