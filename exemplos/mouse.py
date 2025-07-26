import bot

"""
Posição
"""
bot.mouse.posicao_atual()       # Posição atual do mouse na tela
p = bot.mouse.posicao_central() # Posição central na tela


"""
Movimento
"""
c = bot.estruturas.Coordenada.tela()
# Mover o mouse, de forma instantânea, até a `coordenada`
bot.mouse.mover_mouse(coordenada=p) # Posição `(int, int)`
bot.mouse.mover_mouse(coordenada=c) # Coordenada, transformado para a posição no centro da coordenada

# Mover o mouse, deslizando pixel por pixel, até a `coordenada`
bot.mouse.mover_mouse_deslizando(coordenada=p)
bot.mouse.mover_mouse_deslizando(coordenada=c)


"""
Clicar
"""
bot.mouse.clicar_mouse(
    botao = "left",     # Literal['left', 'middle', 'right']
    quantidade = 1,     # Quantidade de clicks
    coordenada = None,  # Mover até a `coordenada` opcionalmente
    delay = 0.1         # Delay aplicado após 1 click
)


"""
Scroll
"""
bot.mouse.scroll_vertical(
    quantidade = 1,     # Quantidade de clicks
    direcao = "baixo",  # Literal['cima', 'baixo']
    coordenada = None,  # Mover até a `coordenada` opcionalmente
    delay = 0.1         # Delay aplicado após 1 click
)
