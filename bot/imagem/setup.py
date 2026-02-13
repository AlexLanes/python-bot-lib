# std
from __future__ import annotations
import time, base64, collections
import tkinter, tempfile, typing
# interno
import bot
from bot.estruturas import Coordenada
# externo
import cv2, numpy as np
import win32gui, win32ui, win32con

def cor_similar (cor1: bot.tipagem.rgb, cor2: bot.tipagem.rgb, tolerancia=20) -> bool:
    """Comparar se as cores `rgb` são similares com base na `tolerancia`
    - `tolerancia mínima` 0 (Cores são idênticas)
    - `tolerancia máxima` 441 (Branco x Preto)"""
    return bool(np.linalg.norm(np.array(cor1) - np.array(cor2)) < tolerancia)

def capturar_tela (regiao: Coordenada | None = None, cinza=False) -> Imagem:
    """Capturar imagem da tela na `regiao` informada e transformar para `cinza` se requisitado"""
    imagem = object().__new__(Imagem)
    x, y, largura, altura = regiao or Coordenada.tela()

    # criar um dispositivo de contexto (DC) compatível e capturar a tela
    desktop = win32gui.GetDesktopWindow()
    desktop_dc = win32gui.GetWindowDC(desktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()
    # criar um objeto bitmap
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, largura, altura)
    mem_dc.SelectObject(screenshot)
    # copiar a tela para o DC da memória
    mem_dc.BitBlt((0, 0), (largura, altura), img_dc, (x, y), win32con.SRCCOPY)
    # obter os dados do bitmap
    bmpstr = screenshot.GetBitmapBits(True)

    # dealocar
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())
    img_dc.DeleteDC()
    win32gui.ReleaseDC(desktop, desktop_dc)

    # transformar para numpy e converter cor
    imagem.pixels = np.frombuffer(bmpstr, dtype=np.uint8)
    imagem.pixels.shape = (altura, largura, 4)
    cor = cv2.COLOR_BGRA2GRAY if cinza else cv2.COLOR_BGRA2BGR
    imagem.pixels = cv2.cvtColor(imagem.pixels, cor)
    return imagem

class Imagem:
    """Classe para manipulação e procura de imagem

    ### Inicialização
    ```
    imagem = Imagem("caminho.png")
    Imagem(bot.sistema.Caminho("caminho.png"))
    Imagem.from_bytes(b"")
    Imagem.from_base64("")
    ```

    ### Transformações
    ```
    imagem.png -> bytes
    imagem.png_base64           # Codificar a imagem para `data:image/png;base64`
    imagem.copiar()             # Criar uma cópia da imagem
    imagem.recortar(Coordenada) # Criar uma nova imagem recortada
    imagem.cinza()              # Criar uma nova imagem como cinza
    imagem.binarizar()          # Criar uma nova imagem binaria
    imagem.inverter()           # Criar uma nova imagem com as cores invertidas
    imagem.redimensionar(float) # Criar uma nova imagem redimensionada para a % `escala`
    ```

    ### Sistema
    ```
    imagem.salvar(caminho)  # Salvar a imagem como arquivo no `caminho`
    imagem.exibir()         # Exibir a imagem em uma janela
    ```

    ### Cores
    ```
    imagem.cores(limite=10)     # Obter a cor RGB e frequência de cada pixel da imagem
    imagem.cor_pixel(posicao)   # Obter a cor RGB do pixel na `posicao`
    imagem.encontrar_cor(rgb)   # Encontrar a posição `(x, y)` de um pixel que tenha a `cor` rgb
    ```

    ### Procura de Imagem
    ```
    imagem.procurar_imagem(...)  # Procurar a coordenada em que a imagem aparece na `referencia` ou tela caso `None`
    imagem.procurar_imagens(...) # Procurar as coordenadas em que a imagem aparece na `referencia` ou tela caso `None`
    ```
    """

    pixels: np.ndarray
    """Pixels da imagem BGR ou Cinza"""

    def __init__ (self, caminho: bot.sistema.Caminho | str) -> None:
        caminho = bot.sistema.Caminho(str(caminho))
        assert caminho.existe(), f"Imagem não encontrada {caminho!r}"

        match caminho.sufixo:
            case ".gif":
                vc = cv2.VideoCapture(caminho.string)
                ok, dados = vc.read()
                vc.release()
                assert ok, f"Erro ao ler imagem .gif '{caminho.string}'"
                self.pixels = dados
            case _:
                dados = cv2.imread(caminho.string)
                assert dados is not None, f"Erro ao ler imagem '{caminho.string}'"
                self.pixels = dados

        # remover transparência caso possua
        if len(self.pixels.shape) == 3 and self.pixels.shape[2] == 4:
            self.pixels = cv2.cvtColor(self.pixels, cv2.COLOR_BGRA2BGR)

    def __repr__ (self) -> str:
        shape = self.pixels.shape
        altura, largura, *_ = shape
        canais = shape[2] if len(shape) >= 3 else 1
        return f"<Imagem {largura}x{altura} canais({canais})>"

    def __eq__ (self, other: object) -> bool:
        return np.array_equal(self.pixels, other.pixels) if isinstance(other, Imagem) else False

    @classmethod
    def from_bytes (cls, conteudo: bytes) -> Imagem:
        """Criar uma imagem a partir de bytes do `conteúdo`"""
        imagem = super().__new__(cls)
        conteudo = np.frombuffer(conteudo, np.uint8) # type: ignore
        imagem.pixels = cv2.imdecode(conteudo, cv2.IMREAD_COLOR) # type: ignore
        return imagem

    @classmethod
    def from_base64 (cls, texto: str) -> Imagem:
        """Criar uma imagem a partir do `texto` base64 (com ou sem prefixo)"""
        # remover prefixo "data:image/...;base64," se houver
        if texto.startswith("data"):
            _, texto = texto.split(",")
        return Imagem.from_bytes(
            base64.b64decode(texto)
        )

    @property
    def png (self) -> bytes:
        """Codificar a imagem para `png`"""
        return cv2.imencode(".png", self.pixels)[1].tobytes()

    @property
    def png_base64 (self) -> str:
        """Codificar a imagem para `data:image/png;base64`"""
        return ",".join((
            "data:image/png;base64",
            base64.b64encode(self.png).decode("utf-8")
        ))

    def copiar (self) -> Imagem:
        """Criar uma cópia da imagem"""
        imagem = super().__new__(type(self))
        imagem.pixels = np.array(self.pixels)
        return imagem

    def salvar (self, caminho: bot.sistema.Caminho | str) -> bot.sistema.Caminho:
        """Salvar a imagem como arquivo no `caminho`"""
        caminho = bot.sistema.Caminho(str(caminho))
        cv2.imwrite(caminho.string, self.pixels)
        return caminho

    def exibir (self) -> None:
        """Exibir a imagem em uma janela
        - Aguarda a janela ser fechada para continuar"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as writer:
            writer.write(self.png)
            caminho = writer.name

        root = tkinter.Tk()
        root.title("Imagem")
        imagem = tkinter.PhotoImage(file=caminho)
        label = tkinter.Label(root, image=imagem)
        label.pack()
        root.mainloop()

    def recortar (self, regiao: Coordenada) -> Imagem:
        """Criar uma nova imagem recortada"""
        imagem = super().__new__(type(self))
        x, y, x_direita, y_baixo = regiao.to_box()
        imagem.pixels = self.pixels[y : y_baixo, x : x_direita]
        return imagem

    def cinza (self) -> Imagem:
        """Criar uma nova imagem como cinza
        - Altera os canais RGB por apenas um de escala do cinza"""
        imagem = super().__new__(type(self))
        cinza = len(self.pixels.shape) == 2
        imagem.pixels = np.array(self.pixels) if cinza else cv2.cvtColor(self.pixels, cv2.COLOR_BGR2GRAY)
        return imagem

    def binarizar (self) -> Imagem:
        """Criar uma nova imagem binaria
        - Altera os canais RGB para apenas um de cinza sendo 0 ou 255"""
        imagem = self.cinza()
        _, imagem.pixels = cv2.threshold(imagem.pixels, 0, 255, cv2.THRESH_OTSU)
        return imagem

    def inverter (self) -> Imagem:
        """Criar uma nova imagem com as cores invertidas"""
        imagem = self.copiar()
        imagem.pixels = cv2.bitwise_not(imagem.pixels)
        return imagem

    def redimensionar (self, escala=2.0) -> Imagem:
        """Criar uma nova imagem redimensionada para a % `escala`"""
        imagem = self.copiar()
        altura, largura, *_ = map(lambda x: int(x * escala), self.pixels.shape)
        imagem.pixels = cv2.resize(imagem.pixels, dsize=(largura, altura), interpolation=cv2.INTER_LINEAR)
        return imagem

    def cores (self, limite: int | None = 10) -> list[tuple[bot.tipagem.rgb, int]]:
        """Obter a cor RGB e frequência de cada pixel da imagem
        - `limite` quantidade que será retornada das mais frequentes
        - `for cor, frequencia in imagem.cores()`"""
        cinza = len(self.pixels.shape) == 2
        pixels = self.pixels.flat if cinza else self.pixels.reshape(-1, 3)
        to_rgb = lambda bgr: (int(bgr), int(bgr), int(bgr)) if cinza else (int(bgr[2]), int(bgr[1]), int(bgr[0]))
        return collections.Counter(map(to_rgb, pixels)).most_common(limite)

    def cor_pixel (self, posicao: tuple[int, int]) -> bot.tipagem.rgb:
        """Obter a cor RGB do pixel na `posicao`"""
        cinza = len(self.pixels.shape) == 2
        to_rgb = lambda bgr: (int(bgr), int(bgr), int(bgr)) if cinza else (int(bgr[2]), int(bgr[1]), int(bgr[0]))
        pixel = self.pixels[posicao[1], posicao[0]]
        return to_rgb(pixel)

    def encontrar_cor (
            self,
            cor: bot.tipagem.rgb,
            modo: typing.Literal["primeiro", "ultimo", "media"] = "media"
        ) -> tuple[int, int] | None:
        """Encontrar a posição `(x, y)` de um pixel que tenha a `cor` rgb
        - `None` caso não encontrado"""
        r, g, b = cor
        bgr = (b, g, r)

        # Encontrar as posicoes
        mask = np.all(self.pixels == bgr, axis=-1)
        posicoes = np.argwhere(mask)
        if posicoes.size == 0:
            return None

        match modo:
            case "primeiro":
                y, x = posicoes[0]
                return (x, y)
            case "ultimo":
                y, x = posicoes[-1]
                return (x, y)
            case "media":
                y_mean, x_mean = posicoes.mean(axis=0)
                return (int(round(x_mean)), int(round(y_mean)))
            case _:
                raise ValueError(f"Modo '{modo}' inesperado")

    def procurar_imagens (self, confianca: bot.tipagem.PORCENTAGENS = 0.9,
                                regiao: Coordenada | None = None,
                                referencia: Imagem | None = None,
                                cinza = False,
                                segundos = 0,
                                delay = 0.5) -> list[Coordenada]:
        """Procurar as coordenadas em que a imagem aparece na `referencia` ou tela caso `None`
        - `confianca` porcentagem de certeza
        - `regiao` especifica uma parte da tela ou imagem de referência
        - `cinza` compara ambas imagem como cinza (mais rápido)
        - `segundos` tempo de procura, a cada `delay` segundos, caso não encontre na primeira vez"""
        confianca = float(confianca)
        segundos, delay = (max(0, n) for n in (segundos, delay))

        np_imagem = (self.cinza() if cinza else self).pixels
        altura, largura, *_ = np_imagem.shape
        x_offset, y_offset, *_ = regiao or (0, 0)

        if referencia and cinza: referencia = referencia.cinza()
        if referencia and regiao: referencia = referencia.recortar(regiao)

        cronometro = bot.tempo.Cronometro()
        confianca_coordenadas = bot.estruturas.PriorityQueue[tuple[float, Coordenada]](comparador=lambda item: item[0])
        while not confianca_coordenadas:
            np_referencia = (referencia or capturar_tela(regiao, cinza)).pixels
            resultado = cv2.matchTemplate(np_imagem, np_referencia, cv2.TM_CCOEFF_NORMED)
            posicoes_confianca = np.where(resultado >= confianca) # type: ignore

            # criar as coordenadas e filtrar possíveis coordenadas com o centro dentro de outra
            for y, x, *_ in zip(*posicoes_confianca):
                coordenada = Coordenada(x + x_offset, y + y_offset, largura, altura)
                if any(c in coordenada for _, c in confianca_coordenadas): continue
                confianca = float(resultado[y, x])
                confianca_coordenadas.add((confianca, coordenada))

            if segundos and not confianca_coordenadas: time.sleep(delay)
            if cronometro() > segundos: break

        return [c for _, c in confianca_coordenadas]

    def procurar_imagem (self, confianca: bot.tipagem.PORCENTAGENS = 0.9,
                               regiao: Coordenada | None = None,
                               referencia: Imagem | None = None,
                               cinza = False,
                               segundos = 0,
                               delay = 0.5) -> Coordenada | None:
        """Procurar a coordenada em que a imagem aparece na `referencia` ou tela caso `None`
        - `confianca` porcentagem de certeza
        - `regiao` especifica uma parte da tela ou imagem de referência
        - `cinza` compara ambas imagem como cinza (mais rápido)
        - `segundos` tempo de procura, a cada `delay` segundos, caso não encontre na primeira vez"""
        return (self.procurar_imagens(confianca, regiao, referencia, cinza, segundos, delay) or [None])[0]

__all__ = [
    "Imagem",
    "Coordenada",
    "cor_similar",
    "capturar_tela"
]