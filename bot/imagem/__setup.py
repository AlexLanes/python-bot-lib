# std
from io import BytesIO
from time import perf_counter
# interno
import bot
from bot.tipagem import Coordenada
# externo
import pyscreeze
import numpy as np
from PIL import Image


pyscreeze.USE_IMAGE_NOT_FOUND_EXCEPTION = False


def transformar_pillow (imagem: str | Image.Image | bytes) -> Image.Image:
    """Receber o formato esperado e transformar para uma imagem do `pillow`"""
    if isinstance(imagem, str): return Image.open(imagem)
    if isinstance(imagem, bytes): return Image.open(BytesIO(imagem))
    return imagem


def capturar_tela (regiao: Coordenada = None, cinza=False) -> Image.Image:
    """Realizar uma captura de tela
    - `regiao` especifica uma parte da tela
    - `cinza` transforma a imagem para o formato grayscale"""
    imagem = pyscreeze.screenshot(region=tuple(regiao) if regiao else None)
    return imagem.convert("L") if cinza else imagem


def procurar_imagem (imagem: bot.tipagem.caminho | Image.Image | bytes, confianca: bot.tipagem.PORCENTAGENS = "0.9", segundos=0, regiao: Coordenada = None, cinza=False) -> Coordenada | None:
    """Procurar a `imagem` na tela, com `confianca`% de confiança na procura e na `regiao` da tela informada
    - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
    - `regiao` especifica uma parte da tela
    - `segundos` tempo de procuraa pela imagem
    - `cinza` compara ambas imagem como grayscale"""
    imagem = transformar_pillow(imagem)
    box = pyscreeze.locateOnScreen(
        image=imagem, 
        minSearchTime=segundos,
        confidence=confianca,
        region=tuple(regiao) if regiao else None,
        grayscale=cinza
    )
    return Coordenada(box.left, box.top, box.width, box.height) if box else None


def procurar_imagens (imagem: bot.tipagem.caminho | Image.Image | bytes, confianca: bot.tipagem.PORCENTAGENS = "0.9", regiao: Coordenada = None, cinza=False) -> list[Coordenada] | None:
    """Procurar todas as vezes que a `imagem` aparece na tela, com `confianca`% de confiança na procura e na `regiao` da tela informada
    - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
    - `regiao` especifica uma parte da tela
    - `cinza` compara ambas imagem como grayscale"""
    imagem = transformar_pillow(imagem)
    boxes = list(pyscreeze.locateAllOnScreen(imagem, 
                                             grayscale=cinza,
                                             confidence=confianca,
                                             region=tuple(regiao) if regiao else None))
    if not boxes: return None # não encontrou

    coordenadas: list[Coordenada] = []
    for box in boxes:
        coordenada = Coordenada(box.left, box.top, box.width, box.height) # transformar para Coordenada
        if all(coordenada not in c for c in coordenadas): # filtrar duplicações
            coordenadas.append(coordenada) # adicionar

    return coordenadas


def cores_imagem (imagem: bot.tipagem.caminho | Image.Image | bytes, limite: int | slice = 10) -> list[tuple[int, tuple[int, int, int]]]:
    """Obter as cores RGB e frequencia de cada pixel da `imagem`
    - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
    - `limite` quantidade que será retornada dos mais frequentes
    - `for (frequencia, cor) in cores_imagem()`"""
    if limite != None and limite <= 0: return []
    imagem = transformar_pillow(imagem)
    itens: list[tuple[int, tuple[int, int, int]]] = imagem.getcolors(10000) # extrair cores
    itens.sort(key=lambda item: item[0], reverse=True) # ordernar pelos mais frequentes
    limite = limite if isinstance(limite, slice) else slice(limite) # criar o slice de limite
    return itens[limite]


class LeitorOCR:
    """Classe de abstração do EasyOCR"""
    
    def __init__ (self, confianca: bot.tipagem.PORCENTAGENS = "0.4"):
        """Inicia o leitor OCR
        - `confianca` porcentagem mínima de confiança no texto extraído (entre 0.0 e 1.0)"""
        from easyocr import Reader
        self.__reader = Reader(["en"])
        
        confianca: float = float(confianca)
        self.__confianca = max(0.0, min(1.0, confianca))
    
    def ler_tela (self, regiao: Coordenada = None) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas da tela na posição `coordenada` 
        - `regiao` vazia para ler a tela inteira
        - `for texto, coordenada in leitor.ler_tela()`"""
        inicio = perf_counter()
        bot.logger.debug("Iniciado o processo de extração de textos e coordenadas da tela")
        
        imagem = capturar_tela(regiao, True)
        extracoes = self.__extrair(imagem)

        # corrigir offset com a regiao informada
        for _, coordenada in extracoes:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y

        bot.logger.debug(f"Extração realizada em {perf_counter() - inicio:.2f} segundos")
        return extracoes

    def ler_imagem (self, imagem: bot.tipagem.caminho | Image.Image | bytes) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas de uma imagem
        - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
        - `for texto, coordenada in leitor.ler_imagem()`"""
        inicio = perf_counter()
        bot.logger.debug("Iniciado o processo de extração de textos e coordenadas de uma imagem")
        
        imagem = transformar_pillow(imagem)
        extracoes = self.__extrair(imagem)

        bot.logger.debug(f"Extração realizada em {perf_counter() - inicio:.2f} segundos")
        return extracoes

    def __extrair (self, imagem: Image.Image) -> list[tuple[str, Coordenada]]:
        """Receber a imagem e extrair os dados"""
        extracoes: list[tuple[str, Coordenada]] = []
        imagem: np.ndarray = np.asarray(imagem)
        dados: list[tuple[ list[list[int]], str, float ]] = self.__reader.readtext(imagem)

        for box, texto, confianca in dados:
            if confianca < self.__confianca: continue
            x, y = box[0]
            comprimento, altura = box[1][0] - x, box[2][1] - y
            extracoes.append((texto, Coordenada(int(x), int(y), int(comprimento), int(altura))))

        return extracoes


__all__ = [
    "LeitorOCR",
    "cores_imagem",
    "capturar_tela",
    "procurar_imagem",
    "procurar_imagens"
]
