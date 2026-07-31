## Biblioteca com funcionalidades gerais para criação de automações para o Windows

⚠️ <span style="color: red;"><strong>Python</strong> <code>&gt;=3.12</code></span> ⚠️

> **Instalação via url do release no github:**  
Via pip `pip install https://github.com/AlexLanes/python-bot-lib/releases/download/v7.0/bot-7.0-py3-none-any.whl`  
Via uv `uv add https://github.com/AlexLanes/python-bot-lib/releases/download/v7.0/bot-7.0-py3-none-any.whl`

> **Para referenciar como dependência:**  
Utilizar o link para o arquivo **whl** do release `bot @ https://github.com/AlexLanes/python-bot-lib/releases/download/v7.0/bot-7.0-py3-none-any.whl`  
Utilizar o caminho para o arquivo **whl** baixado `bot @ file://.../bot-7.0-py3-none-any.whl`

> Os pacotes podem ser encontrados diretamentes no namespace **bot** após import da biblioteca **import bot** ou importado diretamente o pacote desejado **from bot import pacote**


## Changelog 🔧

<details>
<summary>v7.1</summary>

- Removido acessor de elemento `__getattr__` e alterado `__getitem__` na `JanelaW32` e `ElementoW32`
- Incluído novos acessores de elementos `/ // > >> <<` na `JanelaW32` e `ElementoW32`
- Adicionado método no `abrir_abas()` e removido propriedades do `ElementoUIA`

</details>
<details>
<summary>v7.0</summary>

- Alterado formato para `PascalCase` de diversos métodos que são `@classmethod`
- Alterado pacote `email` para se obter e modificar emails
- Alterado pacote `sistema` na manipulação da `Resolucao` e `AbrirProcesso`
- Alterado pacote `configfile` e renomeado variável de acesso para `bot.config`
- Alterado `formatos.Unmarshaller` para usar dependência `msgspec`
- Alterado `formatos.Json` pelas funções `stringify` `validar` `decode`
- Alterado pacote `database` para ser opcional e usar dependência `sqlize`

</details>
<details>
<summary>v6.0</summary>

- Alterado `formatos.Unmarshaller` para user dependência `msgspec`
- Alterado comportamento do `ResultadoSQL`
- Alterado pacotes `imagem` `navegador` `dataset` para serem opcionais devido ao tamanho das dependências
- Alterado métodos do `Navegador` e adicionado outros
- Alterado handlers do `logger` para diminuir o tamanho do `stdout`

</details>
<details>
<summary>v5.1</summary>

- Removido `undetected-chromedriver`
- Adicionado construtores do `Navegador` e suporte ao `with`
- Alterado implementações `Edge` `Chrome`
- Alterado forma de se obter `linhas_afetadas` para o `ResultadoSQL`

</details>
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

### Exemplo
```
[LOGIN]
usuario = rpa
senha = 123

[email]
usuario = ${LOGIN:usuario}@gmail.com
ativado = True
```

### Utilização
```python
import bot

print("Secões", bot.config.secoes())
assert "minha_secao" in bot.config

secao = bot.config.minha_secao
print(secao)
print("Opções Seção", secao.opcoes())

if "usuario" in secao:
    print(secao.usuario)
print(secao.obter_ou("usuario", default=""))
a, b, c = secao.obter("a", "b", "c")
```

### `database`
Pacote para suporte a operações em banco de dados.  
Suporte para construção e execução de `Statement` em múltiplas conexões
### Dependência `bot[database]` necessária para utilizar `bot.database`
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

### `dataset`
Pacote para ler e escrever dados estruturados como `xlsx` e `csv`  
> Exportado `DataFrame` do pacote `polars`
### Dependência `bot[dataset]` necessária para utilizar `bot.dataset`

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

# Criar uma conexão IMAP para realizar a leitura / modificações em Emails
with CaixaEntradaIMAP(usuario="", senha="") as caixa:
    for email in caixa.obter(1, mais_recentes=True):
        print(email)
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
# Validar se o `item` possui o `formato`
def validar[T] (item: object, formato: type[T]) -> bool: ...

# Formatar o `item` para `JSON String`
def stringify (item: object, *, indentar: bool = False) -> str: ...

# Realizar o decode do `item`, em seu formato `str` `bytes`, usando o `decoder` informado
def decode[T] (item: str | bytes, *,
               decoder: Literal["json", "toml", "yaml"] = "json",
               formato: type[T] | Any = Any) -> T:

# Classe Base usada para transformação de um `dict` para uma Classe Modelo
class Dados (Unmarshaller):
    id: int
    nome: str
dados: Dados = Dados.Unmarshal({"id": 1, "nome": "Alex"})

# Classe de manipulação do XML
ElementoXML.Parse(xml: str | Caminho) -> ElementoXML
ElementoXML(
    nome: str,
    texto: str | None = None,
    namespace: tipagem.url | None = None,
    atributos: dict[str, str] | None = None
)
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
### Dependência `bot[imagem]` necessária para utilizar `Imagem`

```python
# Classe para manipulação e procura de imagem
Imagem(caminho: Caminho | str)
Imagem.FromBase64(str)
Imagem.FromBytes(bytes)

# Capturar imagem da tela na `regiao` informada e transformar para `cinza` se requisitado
capturar_tela(
    regiao: Coordenada | None = None,
    cinza = False
) -> Imagem
```

### Dependência `bot[ocr]` necessária para utilizar `LeitorOCR` e `Imagem`
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
logger = MainLogger("MEU_LOG")             # 1
logger = bot.logger.ObterLogger("MEU_LOG") # 2

# Necessário inicializar manualmente em algum logger para configurar os handlers e formato
logger.inicializar()

# Obter o `TracerLogger` utilizado para realizar o rastreamento de um processo
# Possível de se realizar os logs com a mesma interface que o `MainLogger`
from bot.logger.interfaces import TracerLogger
tracer: TracerLogger = logger.obter_tracer(chave="")
# Sinalizar o encerramento do tracer
tracer.encerrar("SUCCESS", "Sucesso ao se realizar determinada Ação")
tracer.encerrar("ERROR", "Falha ao realizar determinada Ação")
# Pode ser usado com o with para encerramento automático
with logger.obter_tracer(chave="") as tracer: ...

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
Pacote para Navegadore Web utilizando o `selenium` como abstração.
> Navegadores são abertos em sua inicialização e fechados quando a sua referencia sair do escopo ou caso seja feito `del navegador`.  
> Possível de se utilizar com o `with` para encerrar automaticamente

### Dependência `bot[navegador]` necessária para utilizar `bot.navegador`

```python
# Navegador Edge
with Edge(...) as navegador: ...
Edge(
    timeout = 30.0,
    download: str | Caminho = "./downloads",
    options_callback: Callable[[EdgeOptions], None] | None = None
)

# Navegador Chrome
with Chrome(...) as navegador: ...
Chrome(
    timeout = 30.0,
    download: str | Caminho = "./downloads",
    options_callback: Callable[[ChromeOptions], None] | None = None
)

# Navegador custom
Navegador.FromDriver(driver: ChromiumDriver, ...)
Navegador.FromChromiumBinary("caminho", ...)

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
Caminho.DiretorioExecucao() / "arquivo.txt"

# Executar um comando com os `argumentos` no `prompt` e aguardar finalizar
executar(
    *argumentos: str,
    powershell: bool = False,
    timeout: float | None = None
) -> tuple[bool, str]

# Obter informações e realizar modificações da resolução da tela
r = Resolucao()
r == "1920x1080"
r.alterar(1920, 1080)

# Encerrar os processos do usuário atual que comecem com algum nome em `nome_processo`
encerrar_processos_usuario (*nome_processo: str) -> int

# Classe para manipulação de janelas e elementos para o backend Win32 e UIA
# docstring das classes com mais informações sobre a utilização
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

# Obter `Datetime` conforme `Timezone` desejado
datetime_brt()
datetime_utc()

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
gravador = GravadorTela().registrar_limpeza_diretorio().iniciar()
...
caminho = gravador.parar()
# a gravação ficará aberta até o fim do Python caso não encerrada manualmente
```