import bot

"""
Funções
"""
bot.sistema.executar()                      # Executar um comando com os argumentos no prompt e aguardar finalizar
bot.sistema.abrir_programa()                # Abrir um programa em um novo processo descolado da `main thread`
bot.sistema.encerrar_processos_usuario()    # Encerrar os processos do usuário atual que comecem com algum nome em nome_processo

bot.sistema.informacoes_resolucao()         # Obter informações sobre resolução da tela
bot.sistema.alterar_resolucao(1920, 1080)   # Alterar a resolução da tela

bot.sistema.copiar_texto(texto="")          # Substituir o texto copiado da área de transferência pelo texto
bot.sistema.texto_copiado()                 # Obter o texto copiado da área de transferênci



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
# Inicialização 
j = bot.sistema.JanelaW32(lambda j: "título" in j.titulo) # Dinâmico, conforme lambda informado
bot.sistema.JanelaW32.from_foco() # Obter a janela com o foco do sistema

# Atributos
j.titulo            # Texto do elemento
j.class_name        # Classname da janela
j.coordenada        # Coordenada da janela
j.processo          # Processo do módulo `psutil` para controle via `PID`
j.maximizada        # Checar se a janela está maximizada
j.minimizada        # Checar se a janela está minimizada
j.focada            # Checar se a janela está focada
j.fechada           # Checar se a janela está fechada

# Métodos
j.maximizar()           # Maximizar janela
j.minimizar()           # Minimizar janela
j.focar()               # Focar janela
j.fechar()              # Enviar a mensagem de fechar para janela e retornar indicador se fechou corretamente
j.destruir()            # Enviar a mensagem de destruir para janela e retornar indicador se fechou corretamente
j.encerrar()            # Enviar a mensagem de fechar para janela e encerrar pelo processo caso continue aberto
j.aguardar()            # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
j.janelas_processo()    # Janelas do mesmo processo da `janela` mas que estão fora de sua árvore
j.dialogo("")           # Encontrar janela de diálogo com `class_name`
j.popup("")             # Encontrar janela de popup com `class_name`
j.print_arvore()        # Realizar o `print()` da árvore de elementos da janela e das janelas do processo
j.to_uia()              # Obter uma instância da `JanelaW32` como `JanelaUIA`

# Métodos estáticos
bot.sistema.JanelaW32.titulos_janelas_visiveis() # Obter os títulos das janelas visíveis
bot.sistema.JanelaW32.ordernar_elementos_coordenada([]) # Ordenar os `elementos` pela posição Y e X

# Acesso, busca e iteração com elementos
e = j.elemento
e.parente               # Parente do elemento
e.profundidade          # Profundidade do elemento (Começa no 0)
e.texto                 # Texto do elemento
e.class_name            # Classname do elemento
e.coordenada            # Coordenada do elemento
e.visivel               # Checar se o elemento está visível
e.ativo                 # Checar se o elemento está ativo
e.caixa_selecao         # Obter a interface da caixa de seleção de uma `CheckBox`ntrar o primeiro elemento descendente, com a menor profundidade, e de acordo com o `filtro`

e.textos(separador = " | ") # Textos dos descendentes concatenados pelo `separador`
e.sleep(segundos=1)         # Aguardar por `segundos` até continuar a execução
e.aguardar()                # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
e.focar()                   # Focar o elemento
e.clicar()                  # Clicar com o `botão` no centro do elemento
e.apertar("enter")          # Apertar e soltar as `teclas` uma por vez
e.digitar("")               # Digitar o `texto` no elemento
e.atalho("ctrl", "c")       # Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa
e.scroll()                  # Realizar scroll no elemento `quantidade` vezes na `direção`
e.print_arvore()            # Realizar o `print()` da árvore de elementos
e.to_uia()                  # Criar um instância do `ElementoW32` como `ElementoUIA`

e.filhos()                                  # Elementos filhos de primeiro nível
e.descendentes()                            # Todos os elementos descendentes
e.encontrar(lambda e: e.class_name == "")   # Encontrar o primeiro elemento descendente, com a menor profundidade, e de acordo com o filtro
