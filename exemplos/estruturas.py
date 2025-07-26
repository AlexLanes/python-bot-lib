import bot

"""
Coordenada de uma região retangular na tela baseado nos pixels
"""
# Coordenada de uma tela FullHD
coordenada = bot.estruturas.Coordenada(
    x=0,            # `x` Posição horizontal do canto superior esquerdo
    y=0,            # `y` Posição vertical do canto superior esquerdo
    largura=1920,   # `largura` Largura da área, a partir do `x`
    altura=1080     # `altura` Altura da área, a partir do `y`
)
# Transformar a coordenada para um ponto (x, y) de acordo com a porcentagem informada para o (x, y)
# Valores entre 0 (0%) e 1 (100%)
# Exemplo abaixo transforma a coordenada para o ponto central da tela
x, y = coordenada.transformar(xOffset=0.5, yOffset=0.5)



"""
Classe para capturar o `return | Exception` de chamadas de uma função
- Alternativa para não propagar o erro e nem precisar utilizar `try-except`
"""
# Chamando manualmente
resultado = bot.estruturas.Resultado(int, "11")
# Possível de se utilizar como decorador
@bot.estruturas.Resultado.decorador
def funcao (): ...
resultado = funcao()

# Propriedades
resultado.valor                     # Acessar o valor diretamente ou `None` caso tenha apresentado erro
resultado.erro                      # Acessar a `Exception` diretamente ou `None` caso não tenha apresentado erro
# Métodos
resultado.ok()                      # Checar se não houve erro
resposta, erro = resultado.unwrap() # Obter o valor da resposta e erro
resultado.valor_ou(default=0)       # Obter o valor da resposta ou default caso tenha apresentado erro



"""
Classe usada para obter/criar/adicionar chaves de um `dict` como `lower-case`
"""
d = bot.estruturas.LowerDict() # Iniciando vazio
d = bot.estruturas.LowerDict({ "A": 1, "B": 2 }) # Iniciando com valor

d["a"]              # Acessar
d["c"] = 3          # Adicionar/Atualizar
del d["b"]          # Remover
len(d)              # Quantidade de chaves
"a" in d            # Checar existência de chave
for chave in d: ... # Iteração sobre as chaves

# Métodos
d.to_dict()                     # Acessar como `dict`
d.get(chave="a", default=11)    # Obter o valor da `chave` ou `default` caso não existir



"""
Classe para realizar comparações e operações matemáticas com precisão em números com ponto flutuante
- `float` possuiu precisão limitada
"""
decimal = bot.estruturas.Decimal(
    valor = "R$ 1.234,56",
    precisao = 2,
    separador_decimal = ","
)
# Suporta os comparadores == != < <= > >=
decimal == "1234,56"
# Suporta as operações + += - -= * *= / /= // //= % %= ** **=
decimal + 1

# Métodos
decimal.nan()   # Checar se o decimal não é um número
str(decimal)    # Obter verão `str` com o separador decimal informado na criação
decimal.copiar(separador=".", precisao=10)      # Copiar o decimal alterando o separador e/ou precisao
bot.estruturas.Decimal.sum([decimal, decimal])  # Realizar a soma de `n` decimais



"""
Estruturas de filas
"""
# Fist In First Out
bot.estruturas.Queue()
# Last In First Out
bot.estruturas.Stack()
# Lista otimizada para inserção/remoção no começo e fim
bot.estruturas.Deque()
# Queue com prioridade na ordem natural
bot.estruturas.PriorityQueue()
