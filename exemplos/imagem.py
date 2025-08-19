import bot

"""
Classe especializada no tratamento de imagem
"""
# Inicialização
imagem = bot.imagem.Imagem("imagem.jpg")
bot.imagem.Imagem(bot.sistema.Caminho("imagem.png"))
bot.imagem.Imagem.from_bytes(b'')
bot.imagem.Imagem.from_base64('')

# Atributos
imagem.pixels       # Pixels da imagem BGR ou Cinza
imagem.png          # Codificar a imagem para png
imagem.png_base64   # Codificar a imagem para `data:image/png;base64`

# Métodos
imagem.copiar()             # Criar uma cópia da imagem
imagem.salvar(caminho=...)  # Salvar a imagem como arquivo no `caminho`
imagem.exibir()             # Exibir a imagem
imagem.cinza()              # Criar uma nova imagem como cinza
imagem.binarizar()          # Criar uma nova imagem binaria
imagem.cores()              # Obter a cor RGB e frequência de cada pixel da imagem
imagem.cor_pixel((10, 10))  # Obter a cor RGB do pixel na `posicao`
imagem.recortar(bot.estruturas.Coordenada(...)) # Criar uma imagem recortada]
imagem.redimensionar(escala=2)                  # Criar uma nova imagem redimensionada para a % `escala`

# Procurar imagem
imagem.procurar_imagem()    # Procurar a coordenada em que a imagem aparece na `referencia` ou tela caso `None`
imagem.procurar_imagens()   # Procurar as coordenadas em que a imagem aparece na `referencia` ou tela caso `None`



"""
Leitor OCR
Classe de abstração do pacote `EasyOCR` para ler/detectar textos em imagens
"""
leitor = bot.imagem.LeitorOCR()

# Extrair informações (texto, coordenada, confianca) da tela inteira ou parcial
leitor.ler_tela()
leitor.ler_tela(bot.estruturas.Coordenada(...))
# Extrair informações de uma imagem
leitor.ler_imagem(bot.imagem.Imagem(...))

# Extrair coordenadas de textos da tela inteira ou parcial
leitor.detectar_tela()
leitor.detectar_tela(bot.estruturas.Coordenada(...))
# Extrair coordenadas da `imagem`
leitor.detectar_imagem(bot.imagem.Imagem(...))



"""
Capturar tela
"""
bot.imagem.capturar_tela() # Tela inteira
bot.imagem.capturar_tela(cinza=True) # Tela inteira como cinza
bot.imagem.capturar_tela(bot.estruturas.Coordenada(0, 0, 100, 100)) # Porção da tela

"""
Comparar se as cores RGB são similares com base na tolerancia
"""
bot.imagem.cor_similar((10, 10, 10), (10, 10, 20), tolerancia=20)
