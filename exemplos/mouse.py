import bot

"""
Posição
"""
bot.mouse.posicao_atual()            # Posição atual do mouse na tela
p = bot.mouse.posicao_central()      # Posição central da tela
c = bot.estruturas.Coordenada.tela() # Coordenada da tela

"""
Mover o mouse, de forma instantânea, até a coordenada
"""
bot.mouse.mover(p) # Posição `(int, int)`
bot.mouse.mover(c) # Coordenada, transformado para a posição no centro da coordenada

"""
Mover o mouse, pixel por pixel, até a coordenada
"""
bot.mouse.mover_deslizando(p) # Posição `(int, int)`
bot.mouse.mover_deslizando(c) # Coordenada, transformado para a posição no centro da coordenada

"""
Mover o mouse relativamente por x e y pixels
"""
bot.mouse.mover_relativo(x=1,  y=1)  # direita e baixo
bot.mouse.mover_relativo(x=-1, y=-1) # esquerda e cima

"""
Clicar
"""
bot.mouse.clicar(quantidade=1, botao="left") # clicar 1 vez na posição atual com o botão esquerdo
bot.mouse.mover(p).clicar() # mover antes de clicar

"""
Realizar o scroll vertical quantidade vezes para a direcao na posição atual
"""
bot.mouse.scroll_vertical(quantidade=1, direcao="baixo")
bot.mouse.mover(p).scroll_vertical() # mover antes do scroll
