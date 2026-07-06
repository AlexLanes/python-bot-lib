"""Pacote para suporte a operações em banco de dados
## Dependência `bot[database]` necessária para utilizar `bot.database`

- Criação de sintaxe SQL com uma linguagem natural do Python
- Suporte para execução de `Statement` em múltiplas conexões
- Suporte para modelagem de objetos via `ORM`

### Statements
`Select` `Update` `Delete` `Insert` `InsertMany` `Upsert`  
Veja o `docstring` de cada comando para mais informações

### Conexões
`bot.database.conexoes`  
Pacote para manipular diferentes conexões e executar `Statement`.  
Veja o `docstring` do pacote para mais informações

### ORM
`bot.database.orm`  
Pacote para `Object Relational Mapping`  
- `bot.database.orm.introspect` para gerar um modelo automaticamente
- Veja o `docstring` do `bot.database.orm.SQLizer` para mais informações

### Table | Column | Expression
Veja docstring do `E` para uma informação completa da `Expression`

```python
from bot.database import E, A, T

# Tabela
usuarios = T.usuarios
usuarios = T.usuarios.Schema("public")

# Usuarios.nome_coluna
usuarios.nome_coluna
T.usuarios.nome_coluna
# Especial
T.usuarios.Column("nome com espaço")
# Alias
A.All(), A.nome_coluna

# Colunas podem construir Expressions
usuarios.id == 1
usuarios.id + 1
usuarios.nome.Upper()
(usuarios.id == 1) & (usuarios.nome == None)

# Constant Expression
E.CURRENT_TIMESTAMP
E.NULL
E.TRUE
E.Value("1")
```

### Exemplo Select + PostgreSQL
```python
from bot.database import E, A, T, Select
from bot.database.conexoes.postgresql import PostgreSQL

with PostgreSQL.Connect(...) as conn:
    users = T.users
    select = (
        Select(users.id, users.name.Trim().As("user_name"))
        .From(users)
        .Where(users.id == 1)
        .OrderBy(users.id.ASC)
        .Offset(0)
        .Limit(100)
    )
    result = conn.execute(select)
    result.print()
```
"""

try: from sqlize import E, A, T
except ImportError: raise ImportError(
    "Dependência opcional 'bot[database]' necessária. "
    "Instale como 'bot[database]' para utilizar o módulo 'bot.database'"
)
from sqlize.statement import Select, Update, Delete, Insert, InsertMany, Upsert
from . import conexoes, orm