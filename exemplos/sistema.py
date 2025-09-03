import bot
from bot.sistema import JanelaW32

"""
Funções
"""
bot.sistema.executar()                      # Executar um comando com os argumentos no prompt e aguardar finalizar
bot.sistema.abrir_processo()                # Abrir um processo descolado da main thread
bot.sistema.encerrar_processos_usuario()    # Encerrar os processos do usuário atual que comecem com algum nome em nome_processo
bot.sistema.criar_mutex("MUTEX_BOT")        # Criar o mutex `nome_mutex` no sistema (Útil para evitar duplicidade em execução)

bot.sistema.informacoes_resolucao()         # Obter informações sobre resolução da tela
bot.sistema.alterar_resolucao(1920, 1080)   # Alterar a resolução da tela

bot.sistema.copiar_texto(texto="")          # Substituir o texto copiado da área de transferência pelo texto
bot.sistema.texto_copiado()                 # Obter o texto copiado da área de transferência



"""
Classe para representação de caminhos, em sua versão absoluta, 
do sistema operacional e manipulação de arquivos/diretórios
"""
# Inicialização
c = bot.sistema.Caminho("main.py")              # Relativo
bot.sistema.Caminho(r"C:\Projetos\Python\bot")  # Absoluto
bot.sistema.Caminho.diretorio_execucao()        # Obter o caminho para o diretório de execução atual
bot.sistema.Caminho.diretorio_usuario()         # Obter o caminho para o diretório do usuário atual

# Atributos
c.string            # Obter o caminho como string
c.parente           # Obter o caminho para o parente do caminho atual
c.nome              # Nome final do caminho
c.fragmentos        # Fragmentos ordenados do caminho
c.data_criacao      # Data de criação do arquivo ou diretório
c.data_modificao    # Data da última modificação do arquivo ou diretório
c.tamanho           # Tamanho em bytes do arquivo ou diretório

# Métodos
c.existe()              # Checar se o caminho existe
c.arquivo()             # Checar se o caminho existente é de um arquivo
c.diretorio()           # Checar se o caminho existente é de um diretório
c.copiar(...)           # Copiar o arquivo ou diretório do caminho atual para o `diretorio` e retornar o caminho
c.renomear("")          # Renomear o nome final do caminho para `novo_nome` e retornar o caminho
c.mover(...)            # Mover o arquivo ou diretório do caminho atual para o `diretorio` e retornar o caminho
c.criar_diretorios()    # Criar todos os diretórios no caminho atual que não existem
c.apagar_arquivo()      # Apagar o arquivo do caminho atual e retornar ao parente
c.apagar_diretorio()    # Apagar o diretório e conteúdo do caminho atual e retornar ao parente
c.limpar_diretorio()    # Limpar os arquivos e diretórios do diretório atual
c.procurar(...)         # Procurar caminhos de acordo com o `filtro`



"""
Classe para iteração com janelas e elementos nativos do Windows
Utilizado em conjunto com o `inpect.exe` instalado com o SDK do Windows

JanelaW32 - Mais rápido porém mais simples
JanelaUIA - Possui tudo do W32 + algumas coisas específicas
"""

### Criação
janela = JanelaW32.from_foco()                              # Janela focada
JanelaW32(lambda j: "titulo" in j.titulo and j.visivel)     # Procurar a janela com filtro dinâmico
JanelaW32(lambda j: ..., aguardar=10)                       # Aguardar por 10 segundos até encontrar a janela
JanelaW32.iniciar("notepad", shell=True, aguardar=30)       # Iniciar uma janela via novo processo
# Aguardar e obter uma janela (visível) que irá abrir após executar alguma ação
with JanelaW32.aguardar_nova_janela(aguardar=2) as janela:
    ...
print(janela.titulo)

### Importante
"""
- Utilizar sempre o `.visivel` nos filtros para garantir que a `janela/elemento` está aparecendo
- Utilizar `.focar()` após obter uma janela para trazer para frente e aguardar estar responsível
- Utilizar o `.aguardar()` para aguardar a janela/elemento estar responsível
    - Utilizado pelo `.focar()`
    - Utilizado pelos métodos de interação dos elementos
"""

### Propriedades
janela.titulo
janela.class_name
janela.visivel    # Checar se a janela está visível
janela.coordenada # Região na tela da janela
janela.processo   # Processo do módulo `psutil` para controle via `PID`
janela.focada     # Checar se a janela está em primeiro plano
janela.minimizada
janela.maximizada
janela.fechada

### Elementos
# Elemento superior da janela para acessar, procurar e manipular elementos
elemento = janela.elemento
elemento.filhos()           # Filhos imediatos
elemento.descendentes()     # Todos os elementos
elemento.encontrar(...)     # Encontrar o primeiro elemento descendente de acordo com o `filtro`
elemento.clicar("left")     # Clicar com o `botão` no centro do elemento
elemento.digitar("texto")   # Digitar o `texto` no elemento
# Encontrar ordenando pela posição Y e X
primeiro = elemento[0]              # Obter elemento pelo index
primeiro, ultimo = elemento[0, -1]  # Obter elementos pelo index
elemento["texto ou class_name"]     # Obter elemento pelo texto ou class_name
...

### Métodos
janela.maximizar()
janela.minimizar()
janela.focar()              # Trazer a janela para primeiro plano
janela.aguardar()           # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
janela.sleep()              # Aguardar por `segundos` até continuar a execução
janela.janelas_processo()   # Janelas do mesmo processo da `janela`
janela.janela_processo(...) # Obter janela do mesmo processo da `janela` de acordo com o `filtro`
janela.print_arvore()       # Realizar o `print()` da árvore de elementos da janela e das janelas do processo

### Métodos acessores
janela.to_uia()     # Obter uma instância da `JanelaW32` como `JanelaUIA`
janela.dialogo()    # Encontrar janela de diálogo com `class_name`
janela.popup()      # Encontrar janela de popup com `class_name`

### Métodos destrutores
janela.fechar()     # Enviar a mensagem de fechar para janela e retornar indicador se fechou corretamente
janela.destruir()   # Enviar a mensagem de destruir para janela e retornar indicador se fechou corretamente
janela.encerrar()   # Enviar a mensagem de fechar para janela e encerrar pelo processo caso não feche

### Métodos estáticos
JanelaW32.titulos_janelas_visiveis()                  # Obter os títulos das janelas visíveis
JanelaW32.ordernar_elementos_coordenada(elementos=[]) # Ordenar os `elementos` pela posição Y e X