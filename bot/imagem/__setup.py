# std
from io import BytesIO
from time import perf_counter
# interno
import bot
from bot.estruturas import Coordenada
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
    regiao = tuple(regiao) if regiao else None
    boxes = [*pyscreeze.locateAllOnScreen(imagem, grayscale=cinza, confidence=confianca, region=regiao)]
    if not boxes: return None # não encontrou

    coordenadas: list[Coordenada] = []
    for box in boxes:
        coordenada = Coordenada(box.left, box.top, box.width, box.height) # transformar para Coordenada
        if all(coordenada not in c for c in coordenadas): # filtrar duplicações
            coordenadas.append(coordenada) # adicionar

    return coordenadas


def obter_cores_imagem (imagem: bot.tipagem.caminho | Image.Image | bytes, limite: int | slice = 10) -> list[tuple[int, tuple[int, int, int]]]:
    """Obter as cores RGB e frequencia de cada pixel da `imagem`
    - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
    - `limite` quantidade que será retornada dos mais frequentes
    - `for (frequencia, cor) in obter_cores_imagem()`"""
    # extrair cores
    imagem = transformar_pillow(imagem)
    itens = [(frequencia, (r, g, b)) for frequencia, (r, g, b, *_) in imagem.getcolors(10000)]
    itens.sort(key=lambda item: item[0], reverse=True) # ordernar pelos mais frequentes
    
    # aplicar o slice
    limite = limite if isinstance(limite, slice) else slice(limite) 
    itens = itens[limite]

    return itens


class LeitorOCR:
    """Classe de abstração do EasyOCR
    - Caso possua GPU da NVIDIA, instalar o `CUDA Toolkit` e instalar as bibliotecas indicadas pelo pytorch https://pytorch.org/get-started/locally/"""

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
        imagem = capturar_tela(regiao, True)
        extracoes = self.__ler(imagem)

        # corrigir offset com a regiao informada
        for _, coordenada in extracoes:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y

        bot.logger.debug(f"Leitura da tela realizada em { bot.util.expandir_tempo(perf_counter() - inicio) }")
        return extracoes

    def ler_imagem (self, imagem: bot.tipagem.caminho | Image.Image | bytes) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas de uma imagem
        - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
        - `for texto, coordenada in leitor.ler_imagem()`"""
        inicio = perf_counter()
        imagem = transformar_pillow(imagem)
        extracoes = self.__ler(imagem)
        bot.logger.debug(f"Leitura da imagem realizada em { bot.util.expandir_tempo(perf_counter() - inicio) }")
        return extracoes

    def __ler (self, imagem: Image.Image) -> list[tuple[str, Coordenada]]:
        """Receber a imagem e extrair os dados"""
        imagem: np.ndarray = np.asarray(imagem)
        extracoes: list[tuple[str, Coordenada]] = []
        dados: list[tuple[ list[list[int]], str, float ]] = self.__reader.readtext(imagem, width_ths=0.7, mag_ratio=2, min_size=5)

        for box, texto, confianca in dados:
            if confianca < self.__confianca: continue
            x, y = box[0]
            comprimento, altura = box[1][0] - x, box[2][1] - y
            extracoes.append((texto, Coordenada(int(x), int(y), int(comprimento), int(altura))))

        return extracoes

    def detectar_imagem (self, imagem: bot.tipagem.caminho | Image.Image | bytes) -> list[Coordenada]:
        """Extrair coordenadas de uma imagem
        - `imagem` pode ser o caminho até o arquivo, bytes da image ou `Image` do módulo `pillow`
        - `confiança` não se aplica na detecção"""
        inicio = perf_counter()
        imagem = transformar_pillow(imagem)
        coordenadas = self.__detectar(imagem)
        bot.logger.debug(f"Imagem detectada em { bot.util.expandir_tempo(perf_counter() - inicio) }")
        return coordenadas

    def detectar_tela (self, regiao: Coordenada = None) -> list[Coordenada]:
        """Extrair coordenadas da tela
        - `regiao` vazia para ler a tela inteira
        - `confiança` não se aplica na detecção"""
        inicio = perf_counter()
        imagem = capturar_tela(regiao, True)
        coordenadas = self.__detectar(imagem)

        # corrigir offset com a regiao informada
        for coordenada in coordenadas:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y

        bot.logger.debug(f"Tela detectada em { bot.util.expandir_tempo(perf_counter() - inicio) }")
        return coordenadas

    def __detectar (self, imagem: Image.Image) -> list[Coordenada]:
        """Receber a imagem e detectar as coordenadas"""
        imagem: np.ndarray = np.asarray(imagem)
        boxes, _ = self.__reader.detect(imagem, threshold=self.__confianca, min_size=5, width_ths=0.7, mag_ratio=2)
        boxes: list[tuple[np.int16, ...]] = np.concatenate(boxes, dtype=np.int16)

        coordenadas = []
        for box in boxes:
            a, b, c, d = (int(posicao) for posicao in box)
            coordenadas.append(Coordenada(x=a, y=c, largura=b - a, altura=d - c))

        return coordenadas


__all__ = [
    "LeitorOCR",
    "capturar_tela",
    "procurar_imagem",
    "procurar_imagens",
    "obter_cores_imagem"
]
