## Biblioteca com funcionalidades gerais para criação de automações para o Windows

⚠️ <span style="color: red;"><strong>Python</strong> <code>&gt;=3.12</code></span> ⚠️

> **Instalação via url do release no github:**  
Via pip `pip install https://github.com/AlexLanes/python-bot-lib/releases/download/v5.0/bot-5.0-py3-none-any.whl`  
Via uv `uv add https://github.com/AlexLanes/python-bot-lib/releases/download/v5.0/bot-5.0-py3-none-any.whl`

> **Para referenciar como dependência:**  
Utilizar o link para o arquivo **whl** do release `bot @ https://github.com/AlexLanes/python-bot-lib/releases/download/v5.0/bot-5.0-py3-none-any.whl`  
Utilizar o caminho para o arquivo **whl** baixado `bot @ file://.../bot-5.0-py3-none-any.whl`

> Os pacotes podem ser encontrados diretamentes no namespace **bot** após import da biblioteca **import bot** ou importado diretamente o pacote desejado **from bot import pacote**


## Changelog 🔧

<details>
<summary>v5.0</summary>

- Criado novo pacote `erro`
- Criado novo pacote `tempo`
- Criado novo pacote `dataset`
- Alteração do pacote `logger` para usar formato Json e suporte a um tracer
- Criado classe `String` no pacote `estruturas`
- Alterado classe `LowerDict` para `DictNormalizado` no pacote `estruturas`
- Movido itens do pacote `util` para pacotes específicos
- Corrigido problema de interpolação no `configfile` com o char `$`
- Alteração pacote `http` para extender classes do `httpx`

</details>
<details>
<summary>v4.1</summary>

- Alterado `Popup` em `bot.sistema.janela`
- Implementado hash e eq especial no `ElementoUIA` em `bot.sistema.janela`
- Correção no formato do `bot.logger` ao chamar `limpar_log_raiz()`

</details>
<details>
<summary>v4.0</summary>

- Alterado pacotes `logger`, `configfile`, `mouse` e `teclado` para utilizarem uma classe
- Alteração geral no `estruturas.Resultado` e `formatos.Json`
- Adicionado `sistema.criar_mutex()`
- Renomeado `util.cronometro()` para `util.Cronometro()`
- Incluído execução do `bot.mouse` como módulo `-m`
- Criado nova classe de manipulação de database `bot.database.DatabaseOracle`

</details>
<details>
<summary>v3.2</summary>

- Alterado métodos e descrição das classes `Sqlite` e `DatabaseODBC` no pacote `database`
- Adicionado parâmetro de tempo limite no `bot.video.GravadorTela()` e alterado default do `comprimir` para `False`
- Alterado lógica do `bot.sistema.JanelaW32.focar()`

</details>
<details>
<summary>v3.1</summary>

- Criado o pacote `video`
- Alterado nome do `sistema.abrir_programa` para `abrir_processo`

</details>
<details>
<summary>v3.0</summary>

- Removido dependência do `pywinauto`
- Criado classes próprias para manipulação de Janelas e função para encerrar processos em `bot.sistema`
- Atualizado métodos para encontrar elementos do `Navegador` para uma classe própria

</details>


## Descrição breve dos pacotes com algumas funcionalidades
Veja a descrição dos pacotes para mais detalhes e inspecionar as funções e classes disponíveis para um melhor contexto

### `argumentos`
Pacote para tratar argumentos de inicialização do Python
- Argumentos posicionais devem vir antes dos nomeados
- Argumentos nomeados: `--nome valor`
- Cobrir argumentos com aspas, caso possua espaço
> Exemplo `python main.py posicional_1 "posicional 2" --nome "Alex Lanes"`
```python
# Checar se um argumento nomeado existe
nomeado_existe (nome: str) -> bool

# Obter o valor do argumento `nome` ou `default` caso não exista
nomeado_ou[T] (nome: str, default: T = "") -> T
```

### `configfile`
Pacote para inicialização de variáveis a partir de arquivo de configuração **.ini**
- Para concatenação de valores, utilizar a sintaxe `${opção}` `${seção:opção}`
- `#` ou `;` comenta a linha se tiver no começo
- Arquivos terminados em `.ini` devem estar presente em `DIRETORIO_EXECUCAO`

**Exemplo**
```ini
[LOGIN]
usuario = rpa
senha = 123

[email]
usuario = ${LOGIN:usuario}@gmail.com
ativado = True
```

```python
# Obter múltiplas `opções` de uma `seção`. Erro caso alguma não exista
obter_opcoes_obrigatorias (secao: str, *opcoes: str) -> tuple[str, ...]
usuario, senha = obter_opcoes_obrigatorias("LOGIN", "usuario", "senha")

# Obter `opcao` de uma `secao` do configfile ou `default` caso não exista
obter_opcao_ou[T] (secao: str, opcao: str, default: T = "") -> T
usuario: str = obter_opcao_ou("email", "usuario")
ativado: bool = obter_opcao_ou("email", "ativado", default=False)
```

### `database`
Pacote com abstrações e normalização de operações em databases
```python
# Criar um arquivo excel em `caminho` com os dados informados em `planilhas`
criar_excel (
    caminho: Caminho,
    planilhas: dict[str, polars.DataFrame]
) -> Caminho

# Classe de abstração do módulo `sqlite3`
Sqlite() # Memória
Sqlite(caminho: str | Caminho) # Caminho .db ou .sqlite

# Classe para manipulação de Databases via drivers ODBC
# Testado com PostgreSQL, MySQL e SQLServer
DatabaseODBC(nome_driver: str, **kwargs: str)
DatabaseODBC(
    "PostgreSQL Unicode(x64)",
    uid = "usuário",
    pwd = "senha",
    server = "servidor",
    port = "porta",
    database = "nome do database",
)

# Classe para manipulação do Oracle Database
DatabaseOracle(user="", password="", host="", port="",
               service_name="", instance_name="")
# Pode ser necessário instalar o **Oracle instant client** e informar o `caminho` antes de abrir conexão
# Utilizar o `OracleDatabase.configurar_cliente(caminho)` para problemas de **thick mode**
OracleDatabase.configurar_cliente(caminho)
```

### `dataset`
Pacote para ler e escrever dados estruturados como `xlsx` e `csv`. Exportado o pacote `polars` para utilização de `DataFrames`
```python
# Excel
excel = bot.dataset.Excel("./exemplo.xlsx")
# Ler a `planilha` do excel 
dados = excel.ler_planilha("nome planilha")
# Criar um arquivo excel no `caminho` com os dados informados de `planilhas`
caminho = excel.escrever(
    planilha1 = [{"nome": "a", "valor": 1}, {"nome": "b", "valor": 2}],
    planilha2 = [{"codigo": "a", "descricao": ""}, {"codigo": "b", "descricao": ""}],
)

# Csv
csv = bot.dataset.Csv("./exemplo.csv")
# Ler o csv
dados = csv.ler()
# Criar um arquivo csv no `caminho` com os `dados` informados
caminho = csv.escrever([
    {"nome": "a", "valor": 1},
    {"nome": "b", "valor": 2}
])
```

### `email`
Pacote agregrador de funções para envio e leitura de e-mail
```python
# Enviar email para uma lista de `destinatarios` com `assunto`, `conteudo` e lista de `anexos`
# Utiliza variáveis do `configfile` para conexão
# Retornado um `Resultado` para não propagar `Exception`
enviar_email (
    destinatarios: Iterable[email],
    assunto = "",
    conteudo = "",
    anexos: list[Caminho] = [],
    no_reply: bool = True
) -> Resultado[None]

# Obter e-mails de uma `Inbox`
# Utiliza variáveis do `configfile` para conexão
obter_emails (
    limite: int | slice | None = None,
    query = "ALL",
    visualizar = False
) -> Generator[Email]
```

### `erro`
Pacote agregador de itens para tratativas de `Exceptions`
```python
# Realizar `tentativas` de se chamar uma função e, em caso de erro, aguardar `segundos` e tentar novamente
@retry (
    *erro: type[Exception],
    tentativas = 3,
    segundos = 5,
    ignorar: tuple[type[Exception], ...] = (NotImplementedError,),
    on_error: lambda args, kwargs: ..., = None
)

# Adicionar uma mensagem de prefixo no erro, caso a função resulte em `Exception`
@adicionar_prefixo (prefixo="Erro ao realizar XPTO")
@adicionar_prefixo (lambda args, kwargs: f"Erro ao realizar XPTO com os argumentos: {args}")
```

### `estruturas`
Pacote agregador com estruturas de dados
```python
# Extensão da classe nativa `str` com utilitários adicionais,
# principalmente para operações com expressões regulares e
# normalização de texto
String("xpto").normalizar()
String("xpto").re_search(r"\w+")

# Classe para representar uma parte de uma região na tela
Coordenada(
    x: int,
    y: int,
    largura: int,
    altura: int,
)

# Classe para capturar o resultado ou `Exception` de alguma chamada
Resultado[T](
    funcao: Callable[..., T],
    *args,
    **kwargs
)

# Dicionário que armazena e acessa chaves sempre na forma `String(chave).normalizar()`
DictNormalizado[T](d: Mapping[str, T] | None = None)
```

### `formatos`
Pacote agregador para diferentes tipos de formatos de dados
```python
# Classe para validação e leitura de objetos JSON
Json (item: Any)
Json.parse (json: str) -> Json

# Classe de manipulação do XML
ElementoXML.parse(xml: str | Caminho) -> ElementoXML
ElementoXML(
    nome: str,
    texto: str | None = None,
    namespace: tipagem.url | None = None,
    atributos: dict[str, str] | None = None
)

# Classe para validação e parse de um `dict` para uma classe anotada
Unmarshaller[T] (cls: type[T])
    # Realizar o parse do `item` conforme a classe informada
    .parse(item: dict[str, Any]) -> T
    # Realizar o parse dos `itens` conforme a classe informada
    .parse(item: list[dict[str, Any]]) -> list[T]
```

### `ftp`
Pacote destinado ao protocolo FTP
```python
# Classe de abstração do `ftplib`
# Utiliza variáveis do `configfile` para conexão
FTP()
```

### `http`
Pacote destinado ao protocolo http
```python
# Enviar um request conforme parâmetros
# Retorna um `ResponseHttp` com métodos adicionais ao `httpx.Response`
request(
    metodo: Literal['HEAD', 'OPTIONS', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    url: str,
    query: QueryParamTypes | None = None,
    headers: HeaderTypes | None = None,
    *,
    json: object | None = None,
    conteudo: RequestContent | None = None,
    dados: RequestData | None = None,
    arquivos: RequestFiles | None = None,
    follow_redirects: bool = False,
    timeout: TimeoutTypes = 60,
    verify: str | bool = True
) -> ResponseHttp

# Criar um cliente `HTTP` para realizar requests
# Extensão do `httpx.Client`
# Retorno dos métodos `request, get, post, put, ...` é um `ResponseHttp` com métodos adicionais ao `httpx.Response`
ClienteHttp(
    base_url: URLTypes,
    headers: HeaderTypes | None = None,
    verify: str | bool = True,
    timeout: TimeoutTypes = DEFAULT_TIMEOUT_CONFIG,
    ...
)

# Classe para parse de dados de um URL
Url(url: str)
```

### `imagem`
Pacote agregador para ações envolvendo imagens
```python
# Capturar imagem da tela na `regiao` informada e transformar para `cinza` se requisitado
capturar_tela(
    regiao: Coordenada | None = None,
    cinza = False
)

# Classe para manipulação e procura de imagem
Imagem(caminho: Caminho | str)
```

> Pacote opcional para realizar OCR.  
Necessário realizar a instalação adicional `bot[ocr]`
```Python
# Classe de abstração do pacote `EasyOCR` para ler/detectar textos em imagens
LeitorOCR()
    # Extrair informações da tela
    .ler_tela (regiao: Coordenada | None = None) -> list[tuple[str, Coordenada, float]]
    # Extrair coordenadas de textos da tela
    .detectar_tela (regiao: Coordenada | None = None) -> list[Coordenada]
```

### `logger`
Pacote para realizar e tratar Logs
```python
# Log para diferentes níveis com o nome `BOT`
logger.debug (mensagem: str) -> MainLogger
logger.informar (mensagem: str) -> MainLogger
logger.alertar (mensagem: str) -> MainLogger
logger.erro (mensagem: str, excecao: Exception | None = None) -> MainLogger
# Possível de se passar itens extra com os argumentos nomeados
# Aparecerão na propriedade `extra`
logger.informar (
    mensagem: str,
    # Exemplo
    quantidade = 10,
    itens = [...],
    dados = {...}
) -> MainLogger

# Criar um logger com nome próprio
# Útil para identificar uma execução
from bot.logger.interfaces import MainLogger
logger = MainLogger("MEU_LOG")              # 1
logger = bot.logger.obter_logger("MEU_LOG") # 2

# Necessário inicializar manualmente para configurar os handlers e formato em algum logger
logger.inicializar_logger()

# Obter o `TracerLogger` utilizado para realizar o rastreamento de um processo
# Possível de se realizar os logs com a mesma interface que o `MainLogger`
from bot.logger.interfaces import TracerLogger
tracer: TracerLogger = logger.obter_tracer()
# Sinalizar o encerramento do tracer
tracer.encerrar("SUCCESS", "Sucesso ao se realizar determinada Ação")
tracer.encerrar("ERROR", "Falha ao realizar determinada Ação")

# Loggar o tempo de execução de uma função
@logger.tempo_execucao
```

### `mouse`
Pacote para realizar ações com o mouse
```python
# Mover o mouse, de forma instantânea, até a `coordenada`
mover (coordenada: tuple[int, int] | Coordenada) -> Mouse

# Clicar com o `botão` do mouse `quantidade` vezes na posição atual
clicar (
    quantidade = 1,
    botao: tipagem.BOTOES_MOUSE = "left",
) -> Mouse

# Realizar o scroll vertical `quantidade` vezes para a `direcao` na posição atual
scroll_vertical (
    quantidade = 1,
    direcao: bot.tipagem.DIRECOES_SCROLL = "baixo"
) -> Mouse:
```

Possível de ser executado como módulo para fazer 
um loop de `print()` com a posição e cor da posição atual do mouse
- python -m `bot.mouse`
- uv run -m `bot.mouse`

### `navegador`
Pacote para navegadores Web.  
Navegadores são abertos em sua inicialização e fechados quando a sua referencia sair do escopo ou caso seja feito `del navegador`

```python
# Navegador Edge baseado no `selenium`
Edge(
    timeout = 30.0,
    download: str | sistema.Caminho = "./downloads"
)

# Navegador Chrome baseado no `selenium`
Chrome(
    timeout = 30.0,
    download: str | sistema.Caminho = "./downloads",
    extensoes: list[str | sistema.Caminho] = [],
    perfil: Caminho | str | None = None,
    argumentos_adicionais: list[str] = []
)

# Ambos navegadores compartilham os mesmo métodos e propriedades. Alguns exemplos:
titulo -> str
url -> tipagem.url
titulos() -> list[str]
pesquisar(url: str) -> Self
nova_aba () -> Self
fechar_aba () -> Self
encontrar (localizador: str | enum.Enum) -> ElementoWEB:
procurar (localizador: str | enum.Enum) -> list[ElementoWEB]:
```

### `sistema`
Pacote para realizar ações no sistema operacional
```python
# Classe para representação de caminhos, em sua versão absoluta, do sistema operacional e manipulação de arquivos/diretórios
Caminho("C:/caminho/completo")
Caminho(".", "pasta", "arquivo.txt")
Caminho() / "diretorio" / "arquivo.txt"
Caminho.diretorio_execucao() / "arquivo.txt"

# Executar um comando com os `argumentos` no `prompt` e aguardar finalizar
executar(
    *argumentos: str,
    powershell = False,
    timeout: float | None = None
) -> tuple[bool, str]

# Alterar a resolução da tela
alterar_resolucao (largura: int, altura: int) -> None

# Encerrar os processos do usuário atual que comecem com algum nome em `nome_processo`
encerrar_processos_usuario (*nome_processo: str) -> int

# Classe para manipulação de janelas e elementos para o backend Win32 e UIA
JanelaW32(lambda janela: bool)
JanelaUIA(lambda janela: bool)
```

### `teclado`
Pacote para realizar ações com o teclado
```python
# Pressionar e soltar as `teclas` uma vez
apertar (*teclas: tipagem.BOTOES_TECLADO | tipagem.char) -> Teclado

# Digitar os caracteres no `texto`
digitar (texto: str) -> Teclado

# Pressionar as `teclas` sequencialmente e soltá-las em ordem reversa
atalho (*teclas: tipagem.BOTOES_TECLADO | tipagem.char) -> Teclado
```

### `tempo`
Pacote destinado para ações que envolvam tempo e condições de espera
```python
# Sleep tradicional com padrão de 1 segundo
sleep(segundos=1)

# Repetir a função `condição`, aguardando por `timeout` segundos, até que resulte em `True`
# Retorna um `bool` indicando se a `condição` foi atendida
sucesso = aguardar(
    condicao: lambda: bool(),
    timeout:  int,
    delay =   0.01
)

# Classe para cronometrar o tempo decorrido
cronometro = Cronometro(precisao=3)
while cronometro < 10: ...

# Classe para se observar o tempo de execução e lançar `TimeoutError`
timeout = Timeout("Ação XPTO demorou de mais").horas(1).minutos(30)
while timeout.pendente(): ...
```

### `tipagem`
Pacote para armazenar tipos utilizados pelos demais pacotes

### `util`
Pacote agregador de funções utilitárias

### `video`
Pacote agregador para ações envolvendo vídeos
```python
# Classe para realizar a captura de vídeo da tela utilizando o `ffmpeg`
gravador = GravadorTela().iniciar()
...
caminho = gravador.parar()
```