# std
import io, time, base64
# interno
from .. import util, tipagem
from ..estruturas import Coordenada, Caminho
# externo
import cv2, numpy as np
from PIL import Image, ImageGrab

def parse_pillow (imagem: tipagem.imagem) -> Image.Image:
    """Transformar a `imagem` para uma `Image` do `pillow`"""
    if isinstance(imagem, Caminho): return Image.open(imagem.string)
    if isinstance(imagem, bytes): return Image.open(io.BytesIO(imagem))
    return imagem

def encode_base64 (imagem: tipagem.imagem) -> str:
    """Transformar a imagem para o formato `data:image/png;base64`"""
    buffer, imagem = io.BytesIO(), parse_pillow(imagem)
    imagem.save(buffer, "PNG")
    buffer = buffer.getvalue()
    return ",".join((
        "data:image/png;base64",
        base64.b64encode(buffer).decode("utf-8")
    ))

def binarizar (imagem: tipagem.imagem) -> Image.Image:
    """Aplicar binarização na imagem
    - Pixels serão transformados em preto ou branco"""
    imagem = parse_pillow(imagem)
    imagem = cv2.cvtColor(np.array(imagem), cv2.COLOR_BGR2GRAY)
    imagem = cv2.threshold(imagem, 0, 255, cv2.THRESH_OTSU)[1]
    return Image.fromarray(imagem)

@util.decoradores.retry(tentativas=2, segundos=10)
def capturar_tela (regiao: Coordenada | None = None, cinza=False) -> Image.Image:
    """Realizar uma captura de tela como `Image` do `pillow`
    - `regiao` especifica uma parte da tela
    - `cinza` transforma a imagem para o formato grayscale"""
    imagem = ImageGrab.grab(regiao.to_box() if regiao else None)
    return imagem.convert("L") if cinza else imagem

def procurar_imagens (imagem: tipagem.imagem,
                      confianca = 0.8,
                      regiao: Coordenada | None = None,
                      referencia: tipagem.imagem | None = None,
                      cinza = False,
                      segundos = 0,
                      delay = 0.5) -> list[Coordenada]:
    """Procurar as coordenadas em que a `imagem` aparece na `referencia` ou tela caso `None`
    - `confianca` porcentagem de certeza
    - `regiao` especifica uma parte da tela ou imagem de referência
    - `cinza` compara ambas imagem como grayscale (mais rápido)
    - `segundos` tempo de procura, a cada `delay` segundos, caso não encontre na primeira vez"""
    conversao = "L" if cinza else "RGB"
    box = regiao.to_box() if regiao else None
    segundos, delay = (max(0, n) for n in (segundos, delay))
    np_imagem = np.asarray(parse_pillow(imagem).convert(conversao))
    altura, largura, *_ = np_imagem.shape

    coordenadas = []
    cronometro = util.cronometro()
    while not coordenadas:
        np_referencia = np.asarray(
            parse_pillow(referencia or ImageGrab.grab())
                .crop(box)
                .convert(conversao)
        )
        resultado = np.where(cv2.matchTemplate(np_imagem, np_referencia, cv2.TM_CCOEFF_NORMED) >= confianca)

        # criar as coordenadas e filtrar possíveis coordenadas com o centro dentro de outra
        for (y, x, *_) in zip(*resultado):
            coordenada = Coordenada(x, y, largura, altura)
            if any(c in coordenada for c in coordenadas): continue
            coordenadas.append(coordenada)

        if segundos and not coordenadas: time.sleep(delay)
        if cronometro() > segundos: break

    return coordenadas

def procurar_imagem (imagem: tipagem.imagem,
                     confianca = 0.8,
                     regiao: Coordenada | None = None,
                     referencia: tipagem.imagem | None = None,
                     cinza = False,
                     segundos = 0,
                     delay = 0.5) -> Coordenada | None:
    """Procurar a coordenada em que a `imagem` aparece na `referencia` ou tela caso `None`
    - `confianca` porcentagem de certeza
    - `regiao` especifica uma parte da tela ou imagem de referência
    - `cinza` compara ambas imagem como grayscale (mais rápido)
    - `segundos` tempo de procura, a cada `delay` segundos, caso não encontre na primeira vez"""
    return (procurar_imagens(imagem, confianca, regiao, referencia, cinza, segundos, delay) or [None])[0]

def cor_pixel (posicao: tuple[int, int],
               imagem: tipagem.imagem | None = None) -> tipagem.rgb:
    """Obter a cor RGB na `posicao` da `imagem`
    - `imagem` não pode ser no formato grayscale
    - Captura da tela caso `imagem` seja `None`"""
    imagem = parse_pillow(imagem or capturar_tela())
    return tuple(
        int(cor)
        for index, cor in enumerate(imagem.getpixel(posicao))
        if index < 3
    )

def cores_imagem (imagem: tipagem.imagem, limite: int | slice = 10) -> list[tuple[int, tipagem.rgb]]:
    """Obter a frequência e cor RGB de cada pixel da `imagem`
    - `limite` quantidade que será retornada das mais frequentes
    - `[(frequencia, cor)]`"""
    # extrair cores
    imagem = parse_pillow(imagem)
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
    "cor_pixel",
    "binarizar",
    "Coordenada",
    "cor_similar",
    "cores_imagem",
    "parse_pillow",
    "encode_base64",
    "capturar_tela",
    "procurar_imagem",
    "procurar_imagens",
]
