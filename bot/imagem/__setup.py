# std
from io import BytesIO
# interno
import bot
from bot import tipagem
from bot.estruturas import Coordenada
# externo
import numpy as np
import pyscreeze, cv2
from PIL import Image

pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False

def transformar_pillow (imagem: tipagem.imagem) -> Image.Image:
    """Receber o formato esperado e transformar para uma imagem do `pillow`"""
    if isinstance(imagem, str): return Image.open(imagem)
    if isinstance(imagem, bytes): return Image.open(BytesIO(imagem))
    return imagem

@bot.util.decoradores.retry(2, 10)
def capturar_tela (regiao: Coordenada = None, cinza=False) -> Image.Image:
    """Realizar uma captura de tela
    - `regiao` especifica uma parte da tela
    - `cinza` transforma a imagem para o formato grayscale"""
    imagem = pyscreeze.screenshot(region=tuple(regiao) if regiao else None)
    return imagem.convert("L") if cinza else imagem

def binarizar (imagem: tipagem.imagem) -> Image.Image:
    """Aplicar binarização da imagem
    - Pixels serão transformados em preto ou branco"""
    imagem = transformar_pillow(imagem)
    imagem = cv2.cvtColor(np.array(imagem), cv2.COLOR_BGR2GRAY)
    imagem = cv2.threshold(imagem, 0, 255, cv2.THRESH_OTSU)[1]
    return Image.fromarray(imagem)

def procurar_imagem (imagem: tipagem.imagem,
                     confianca: tipagem.PORCENTAGENS = "0.9",
                     segundos=0,
                     regiao: Coordenada = None,
                     cinza=False) -> Coordenada | None:
    """Procurar a `imagem` na tela, com `confianca`% de confiança na procura e na `regiao` da tela informada
    - `regiao` especifica uma parte da tela
    - `segundos` tempo de procura pela imagem
    - `cinza` compara ambas imagem como grayscale"""
    imagem = transformar_pillow(imagem)
    box = pyscreeze.locateOnScreen(
        image=imagem, 
        minSearchTime=segundos,
        confidence=confianca,
        region=tuple(regiao) if regiao else None,
        grayscale=cinza
    )
    return Coordenada(*box) if box else None

def procurar_imagens (imagem: tipagem.imagem,
                      confianca: tipagem.PORCENTAGENS = "0.9",
                      regiao: Coordenada = None,
                      cinza=False) -> list[Coordenada] | None:
    """Procurar todas as vezes que a `imagem` aparece na tela, com `confianca`% de confiança na procura e na `regiao` da tela informada
    - `regiao` especifica uma parte da tela
    - `cinza` compara ambas imagem como grayscale"""
    imagem = transformar_pillow(imagem)
    regiao = tuple(regiao) if regiao else None
    boxes = [*pyscreeze.locateAllOnScreen(imagem, grayscale=cinza, confidence=confianca, region=regiao)]
    if not boxes: return None # não encontrou

    coordenadas: list[Coordenada] = []
    for box in boxes:
        coordenada = Coordenada(*box) # transformar para Coordenada
        if all(coordenada not in c for c in coordenadas): # filtrar duplicações
            coordenadas.append(coordenada)

    return coordenadas

def cores_imagem (imagem: tipagem.imagem, limite: int | slice = 10) -> list[tuple[int, tipagem.rgb]]:
    """Obter a frequencia e cores RGB de cada pixel da `imagem`
    - `limite` quantidade que será retornada das mais frequentes
    - `for frequencia, cor in cores_imagem()`"""
    # extrair cores
    imagem = transformar_pillow(imagem)
    itens: list[tuple[int, tipagem.rgb]] = [
        (frequencia, (r, g, b)) 
        for frequencia, (r, g, b, *_) in imagem.getcolors(10000)
    ]
    itens.sort(key=lambda item: item[0], reverse=True) # ordernar pelos mais frequentes

    # aplicar o slice
    limite = limite if isinstance(limite, slice) else slice(limite) 
    itens = itens[limite]

    return itens

def cor_similar (cor1: tipagem.rgb, cor2: tipagem.rgb, tolerancia=20) -> bool:
    """Comparar se as cores `rgb` são similares com base na `tolerancia`
    - `tolerancia mínima` 0 (Cores são idênticas)
    - `tolerancia máxima` 441 (Branco x Preto)"""
    return np.linalg.norm(np.array(cor1) - np.array(cor2)) < tolerancia

__all__ = [
    "binarizar",
    "Coordenada",
    "cor_similar",
    "cores_imagem",
    "capturar_tela",
    "procurar_imagem",
    "procurar_imagens"
]
