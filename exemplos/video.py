from bot.video import GravadorTela

"""
Classe para realizar a captura de vídeo da tela utilizado o `ffmpeg`
"""
gravador = GravadorTela()
gravador.iniciar()                          # com nome automático
gravador.iniciar(nome_extensao="xpto.mp4")  # com nome alterado
caminho = gravador.parar() # parar a gravação e obter o caminho para o arquivo

# caso não queira obter o arquivo
# o gravador continuará ativo até o encerramento do Python
GravadorTela().iniciar()