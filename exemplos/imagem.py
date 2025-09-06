import bot
from bot.imagem import Imagem, Coordenada, LeitorOCR


"""
Capturar tela
"""
bot.imagem.capturar_tela() # Tela inteira
bot.imagem.capturar_tela(cinza=True) # Tela inteira como cinza
bot.imagem.capturar_tela(Coordenada(0, 0, 100, 100)) # Porção da tela


"""
Classe para manipulação e procura de imagem
"""
### Inicialização
imagem = Imagem("caminho.png")
Imagem(bot.sistema.Caminho("caminho.png"))
Imagem.from_bytes(b"")
Imagem.from_base64("")

### Transformações
imagem.png                  # bytes
imagem.png_base64           # Codificar a imagem para `data:image/png;base64`
imagem.copiar()             # Criar uma cópia da imagem
imagem.recortar(...)        # Criar uma nova imagem recortada
imagem.cinza()              # Criar uma nova imagem como cinza
imagem.binarizar()          # Criar uma nova imagem binaria
imagem.inverter()           # Criar uma nova imagem com as cores invertidas
imagem.redimensionar(...)   # Criar uma nova imagem redimensionada para a % `escala`

### Sistema
imagem.salvar(...)  # Salvar a imagem como arquivo no `caminho`
imagem.exibir()     # Exibir a imagem em uma janela

### Cores
imagem.cores(limite=10)     # Obter a cor RGB e frequência de cada pixel da imagem
imagem.cor_pixel(...)       # Obter a cor RGB do pixel na `posicao`
imagem.encontrar_cor(...)   # Encontrar a posição `(x, y)` de um pixel que tenha a `cor` rgb

### Procura de Imagem
imagem.procurar_imagem(...)  # Procurar a coordenada em que a imagem aparece na `referencia` ou tela caso `None`
imagem.procurar_imagens(...) # Procurar as coordenadas em que a imagem aparece na `referencia` ou tela caso `None`


"""
Classe de abstração do pacote `EasyOCR` para ler/detectar textos em imagens
#### [Documentação EasyOCR](https://www.jaided.ai/easyocr/documentation)
- `linguagem` linguagens aceitas pelo `EasyOCR`. Default `en` que é mais preciso
- `gpu=True` Caso possua GPU da NVIDIA, instalar o `CUDA Toolkit` e instalar as bibliotecas indicadas pelo [pytorch](https://pytorch.org/get-started/locally)
- Possui alguns parâmetros customizáveis para alterar o leitor e detector
"""
### Inicialização
# Default utilizado a linguagem `en`, que é o mais otimizado, e sem `gpu`
leitor = LeitorOCR()
# O EasyOCR é custoso na inicialização
# Utilizar sistema de cache ou constante para evitar ficar inicializando múltiplas vezes

### Parâmetros
leitor.decoder      # Parâmetro utilizado pela decodificação de textos na leitura
leitor.mag_ratio    # Taxa de ampliação da imagem
leitor.min_size     # Filtrar caixas de texto menor que o valor mínimo em pixels
leitor.slope_ths    # Filtrar caixas de texto menor que o valor mínimo em pixels
leitor.width_ths    # Distância horizontal máxima para mesclar caixas
leitor.allowlist    # Caracteres permitidos a serem retornados pelos métodos de leitura

### Detecção de Coordenadas de textos
leitor.detectar_tela()          # Detectar coordenadas de texto na tela inteira
leitor.detectar_tela(...)       # Detectar coordenadas de texto em parte da tela
leitor.detectar_imagem(imagem)  # Detectar coordenadas de texto na `imagem`
leitor.detectar_linhas(imagem)  # Detectar coordenadas de texto na `imagem` e agrupar pela linha

### Extração de textos
leitor.ler_tela()               # Extrair informações da tela inteira
leitor.ler_tela(...)            # Extrair informações de parte da tela
leitor.ler_imagem(imagem)       # Extrair informações da `imagem`
leitor.ler_texto_imagem(imagem) # Ler e retornar os textos extraídos da `imagem` concatenados
leitor.ler_linhas(imagem)       # Extrair dados da `imagem` concatenando as linhas em uma `str`

# Extrair as colunas e linhas da `imagem` de uma tabela
# Funciona apenas para tabelas com os nomes das colunas `left-align`
leitor.ler_tabela(imagem)                               # Todas as colunas
leitor.ler_tabela(imagem, ("Coluna1", "Coluna2", ...))  # Restringir e corrigir nome das colunas

### Útil
# Pode ser necessário pois o OCR não gera resultados 100% correto
bot.util.encontrar_texto(...)   # Encontrar a melhor opção em `opções` onde igual ou parecido ao `texto`
leitor.encontrar_textos(...)    # Encontrar as coordenadas dos `textos` na `extraçao` retornada pela a leitura da tela ou imagem


"""
Comparar se as cores RGB são similares com base na tolerancia
"""
bot.imagem.cor_similar((10, 10, 10), (10, 10, 20), tolerancia=20)