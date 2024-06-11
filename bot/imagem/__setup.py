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


def procurar_imagem (imagem: tipagem.imagem, confianca: tipagem.PORCENTAGENS = "0.9", segundos=0, regiao: Coordenada = None, cinza=False) -> Coordenada | None:
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


def procurar_imagens (imagem: tipagem.imagem, confianca: tipagem.PORCENTAGENS = "0.9", regiao: Coordenada = None, cinza=False) -> list[Coordenada] | None:
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


class LeitorOCR:
    """Classe de abstração do EasyOCR
    - Caso possua GPU da NVIDIA, instalar o `CUDA Toolkit` e instalar as bibliotecas indicadas pelo pytorch https://pytorch.org/get-started/locally/"""

    def __init__ (self, confianca: tipagem.PORCENTAGENS = "0.4"):
        """Inicia o leitor OCR
        - `confianca` porcentagem mínima de confiança no texto extraído `(entre 0.0 e 1.0)`"""
        from easyocr import Reader
        self.__reader = Reader(["en"])
        self.__confianca = max(0.0, min(1.0, float(confianca)))

    def ler_tela (self, regiao: Coordenada = None) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas da tela na posição `coordenada` 
        - `regiao` vazia para ler a tela inteira
        - `for texto, coordenada in leitor.ler_tela()`"""
        cronometro = bot.util.cronometro()
        extracoes = self.__ler(capturar_tela(regiao, True))

        # corrigir offset com a regiao informada
        for _, coordenada in extracoes:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y

        tempo = bot.util.expandir_tempo(cronometro())
        bot.logger.debug(f"Leitura da tela realizada em {tempo}")
        return extracoes

    def ler_imagem (self, imagem: tipagem.imagem) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas de uma imagem
        - `for texto, coordenada in leitor.ler_imagem()`"""
        cronometro = bot.util.cronometro()
        extracoes = self.__ler(transformar_pillow(imagem))
        tempo = bot.util.expandir_tempo(cronometro())
        bot.logger.debug(f"Leitura da imagem realizada em {tempo}")
        return extracoes

    def __ler (self, imagem: Image.Image) -> list[tuple[str, Coordenada]]:
        """Receber a imagem e extrair os dados"""
        imagem: np.ndarray = np.asarray(imagem)
        return [
            (texto, Coordenada.from_box((box[0][0], box[1][0], box[0][1], box[2][1])))
            for box, texto, confianca in self.__reader.readtext(imagem, mag_ratio=2, min_size=5, slope_ths=0.25, width_ths=0.4)
            if confianca >= self.__confianca
        ]

    def detectar_tela (self, regiao: Coordenada = None) -> list[Coordenada]:
        """Extrair coordenadas da tela
        - `regiao` vazia para ler a tela inteira
        - `confiança` não se aplica na detecção"""
        cronometro = bot.util.cronometro()
        coordenadas = self.__detectar(capturar_tela(regiao, True))

        # corrigir offset com a regiao informada
        for coordenada in coordenadas:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y
    
        tempo = bot.util.expandir_tempo(cronometro())
        bot.logger.debug(f"Tela detectada em {tempo}")
        return coordenadas

    def detectar_imagem (self, imagem: tipagem.imagem) -> list[Coordenada]:
        """Extrair coordenadas de uma imagem
        - `confiança` não se aplica na detecção"""
        cronometro = bot.util.cronometro()
        coordenadas = self.__detectar(transformar_pillow(imagem))
        tempo = bot.util.expandir_tempo(cronometro())
        bot.logger.debug(f"Imagem detectada em {tempo}")
        return coordenadas

    def __detectar (self, imagem: Image.Image) -> list[Coordenada]:
        """Receber a imagem e detectar as coordenadas"""
        imagem: np.ndarray = np.asarray(imagem)
        boxes, _ = self.__reader.detect(imagem, mag_ratio=2, min_size=5, slope_ths=0.25, width_ths=0.4)
        boxes: list[tuple[np.int32, ...]] = np.concatenate(boxes)
        return [
            Coordenada.from_box(box)
            for box in boxes
        ]


__all__ = [
    "binarizar",
    "LeitorOCR",
    "cor_similar",
    "cores_imagem",
    "capturar_tela",
    "procurar_imagem",
    "procurar_imagens"
]
