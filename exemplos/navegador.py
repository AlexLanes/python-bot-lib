import bot

"""
Navegadores
Todos possuem métodos similares pois partem de uma classe base dependente do `selenium`
Argumentos de inicialização modificam o comportamento do navegador (Checar comentário das classes)
"""
n = bot.navegador.Edge(...) # Navegador Edge simplificado e o mais provável de já existir no sistema
bot.navegador.Chrome(...) # Utiliza o `undetected_chromedriver`, em cima do `selenium`, para evitar detecção de automação
bot.navegador.Explorer(...) # Necessário realizar uma pré-configuração conforme descrição da classe


"""
Propriedades
"""
n.driver                # Driver do `selenium`
n.timeout_inicial       # Timeout informado na inicialização da classe
n.diretorio_download    # Diretório de download informado na inicialização da classe
n.titulo                # Título da aba focada
n.url                   # Url da aba focada
n.aba                   # ID da aba focada
n.abas                  # ID das abas abertas


"""
Métodos
"""
n.sleep(segundos=5) # Aguardar n segundos
n.titulos()         # Títulos das abas abertas
n.pesquisar(url="") # Pesquisar o url na aba focada
n.atualizar()       # Atualizar a aba focada
n.nova_aba()        # Abrir uma nova aba e alterar o foco para ela
n.fechar_aba()      # Fechar a aba focada e alterar o foco para a primeira aba
n.limpar_abas()     # Fechar as abas abertas, abrir uma nova e focar
n.imprimir_pdf()    # Imprimir a página/frame atual do navegador para `.pdf`
n.focar_aba(identificador="")            # Focar na aba com base no `identificador`
n.alterar_timeout(timeout=0)             # Alterar o tempo de `timeout` para ações realizadas pelo navegador
n.aguardar_titulo(titulo="", timeout=0)  # Aguardar alguma aba conter o `título` e alterar o foco para ela
n.aguardar_download(".xlsx", timeout=60) # Aguardar um novo arquivo, com nome contendo algum dos `termos`, no diretório de download por `timeout` segundos


"""
Métodos visando elementos
"""
# Encontrar o primeiro elemento na aba atual com base no `localizador`
# Exceção `ElementoNaoEncontrado` caso não seja encontrado
e = n.encontrar("//tbody")  # suporta xpath
n.encontrar("tbody >  tr")  # css selector

# Procurar elemento(s) na aba atual com base no `localizador`
n.procurar("//tbody")       # suporta xpath
n.procurar("tbody >  tr")   # css selector

# Alterar o frame atual do DOM da página para o `frame` contendo `@name, @id ou ElementoWEB`
# Necessário para encontrar e interagir com elementos dentro de `<iframes>`
n.alterar_frame(...)


"""
ElementoWEB
Classe própria retornada pelo `encontrar` e `procurar`
Criada visando evitar os erros contantes de `StaleElementReferenceException`
"""
# Atributos
e.elemento      # Elemento original do `selenium`
e.texto         # Texto do elemento com `strip()`
e.nome          # Nome da `<tag>` do elemento
e.visivel       # Indicador se o elemento está visível
e.ativo         # Indicador se o elemento está habilitado para interação
e.selecionado   # Indicador se o elemento está selecionado
e.select        # Obter a classe de tratamento do elemento `<select>`
e.imagem        # Capturar a imagem do elemento
e.atributos     # Obter os atributos html do elemento

# Métodos
e.sleep()       # Aguardar por `segundos` até continuar a execução
e.hover()       # Realizar a ação de hover no elemento
e.clicar()      # Realizar a ação de click no elemento
e.limpar()      # Limpar o texto do elemento, caso suportado
e.digitar()     # Digitar o texto no elemento
e.encontrar("") # Encontrar o primeiro elemento descendente do `elemento` atual com base no `localizador`
e.procurar("")  # Procurar elemento(s) descendente(s) do `elemento` atual com base no `localizador`

# Condições de espera simples
e.aguardar_clicavel()       # Aguardar condição `element_to_be_clickable` do `elemento` por `timeout` segundos
e.aguardar_visibilidade()   # Aguardar condição `visibility_of` do `elemento` por `timeout` segundos

# Condições de espera com contexto
# Utilizar com o `with` e realizar uma ação que alterará o elemento
with e.aguardar_staleness() as elemento: ...        # Aguardar condição `staleness_of` do `elemento` por `timeout` segundos
with e.aguardar_invisibilidade() as elemento: ...   # Aguardar condição `invisibility_of_element` do `elemento` por `timeout` segundos
with e.aguardar_update() as elemento: ...           # Aguardar update no `outerHTML` do `elemento` por `timeout` segundos
