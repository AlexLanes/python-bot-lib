import bot
from typing import Literal

"""
Unmarshaller
Classe para validação e parse de um `dict` para uma classe customizada
"""
# Classe de exemplo
class Endereco:
    rua: str
    numero: int | None
class EnderecoComComplemento (Endereco):
    complemento: str
class Pessoa:
    nome: str
    idade: int
    sexo: Literal["M", "F"]
    opcional: str | None
    opcional_com_default: str = "default"
    informado_com_default: int | str = "10"
    documentos: dict[str, str | int | None]
    enderecos: list[Endereco | EnderecoComComplemento]

# Realizando o Parse
item = {
    "nome": "Alex",
    "idade": 27,
    "sexo": "M",
    "Informado Com Default": 20,
    "documentos": {"cpf": "123", "rg": None, "cnpj": 1234567 },
    "enderecos": [{ "rua": "rua 1", "numero": 1 }, { "rua": "rua 2", "complemento": "próximo ao x" }],
}
pessoa = bot.formatos.Unmarshaller(Pessoa).parse(item)
print(pessoa)



"""
JSON
Classe para validação e leitura de itens JSON acessando propriedades via `.` ou `[]`
- Conforme Javascript
"""
item = {
    "nome": "Alex",
    "campo com espaço": 20,
    "documentos": { "cpf": "123", "rg": None, "cnpj": 1234567 },
    "enderecos": [{ "rua": "rua 1", "numero": 1 }, { "rua": "rua 2", "complemento": "próximo ao x" }],
}

# Criação
json = bot.formatos.Json.parse('{ "nome": "Alex" }')
json = bot.formatos.Json(item)

# Caminhos válidos
json.nome
json["campo com espaço"]
json.documentos.rg
json.enderecos[0].rua

# Caminhos invalidos
json["errado"]
json.enderecos[2]

# Checar existência do caminho
bool(json.nome)
if json.nome: ...

# Comparações aceitas
json.nome == "Alex"
json.nome != "Alex"
"Alex" in json.nome # Usar em str, list e dict

# Obter o tipo do json
tipo = json.tipo()

# Transformar para string json
json.stringify(indentar=True)

# Acessar o valor do `json` validando com o tipo `esperar`
# Erro caso o caminho seja inválido ou o tipo `esperar` seja inválido
valor = json.nome.obter(str)
valor = json.nome.obter(str | None)
valor = json["campo com espaço"].obter(Literal[20])
valor = json.documentos.obter(dict)
valor = json.enderecos.obter(list[dict[str, dict]])

# Realizar o unmarshal do `item` conforme a `classe`
objeto = json.unmarshal(classe)



"""
XML
Classe de manipulação e criação de XML
"""
from bot.formatos import ElementoXML

# Parse
ElementoXML.parse(bot.sistema.Caminho("arquivo.xml"))
ElementoXML.parse('<raiz versão="1"><filho1>abc</filho1><filho2>xyz</filho2></raiz>')

# Criação de elementos
raiz = ElementoXML("raiz", atributos={ "versão": "1" })
raiz.adicionar(ElementoXML("filho1", "abc"), ElementoXML("filho2", "xyz"))
print(raiz) # <raiz versão="1"><filho1>abc</filho1><filho2>xyz</filho2></raiz>

# Atributos
raiz.nome       # Nome do elemento
raiz.texto      # Texto do elemento (se houver)
raiz.atributos  # Atributos do elemento
raiz.namespace  # Namespace do elemento (se houver)

# Acessores
len(raiz)               # Quantidade de elemento(s) filho(s)
str(raiz)               # Versão `text/xml` do ElementoXML
bool(raiz)              # Formato `bool` indicando se possui algum filho ou texto
for filho in raiz: ...  # Iterator dos `elementos` filhos

# Métodos
raiz.adicionar()    # Adicionar `n` elementos como filho
raiz.inserir()      # Inserir elemento no index informado
raiz.elementos()    # Elementos filhos
raiz.remover()      # Remover elemento descendente do elemento
raiz.indentar()     # Indentar a verão `str()` do xml
raiz.copiar()       # Criar uma cópia do elemento
raiz.to_dict()      # Versão `dict` do elemento

# Localizadores xpath
ElementoXML.registrar_prefixo("ns", "url")  # Registrar um namespace para utilizar na procura com o xpath
raiz.procurar(xpath="", namespaces={})      # Procurar elementos que resultem no xpath informado
raiz.encontrar(xpath="", namespaces={})     # Encontrar elemento que resulte no xpath informado ou None caso não seja encontrado



"""
TOML
Classe para leitura, acesso e validação de tipo do formato `TOML`
- O formato toml aceita os tipos: `str, int, float, bool, dict[str, ...], list[...]`
- `chave` aceita chaves aninhadas. Exemplo `tool."setup tools"`
"""
toml = bot.formatos.Toml("arquivo.toml")
chave = 'tool."setuptools"'
# Checar existência
chave in toml
toml.existe(chave)
# Obter valor sem validação
toml[chave]
# Obter valor com validação
toml.obter(chave, dict[str, str])