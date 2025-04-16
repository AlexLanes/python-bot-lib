# std
import typing, functools
# interno
from .. import util
from . import Coordenada, Imagem, capturar_tela
# externo
import numpy as np

class LeitorOCR:
    """Classe de abstração do pacote `EasyOCR` para ler/detectar textos em imagens
    - Caso possua GPU da NVIDIA, instalar o `CUDA Toolkit` e instalar as bibliotecas indicadas pelo pytorch https://pytorch.org/get-started/locally/"""

    def __init__ (self) -> None:
        try: from easyocr import Reader
        except ImportError: raise ImportError("Pacote opcional [ocr] necessário. Realize `pip install bot[ocr]` para utulizar o LeitorOCR")
        self.__reader = Reader(["en"])

    def ler_tela (self, regiao: Coordenada | None = None) -> list[tuple[str, Coordenada, float]]:
        """Extrair informações da tela
        - `regiao` para limitar a área de extração
        - `for texto, coordenada, confianca in leitor.ler_tela()`"""
        imagem = capturar_tela(regiao, True)
        extracoes = self.__ler(imagem)

        # corrigir offset com a regiao informada
        for _, coordenada, _ in extracoes:
            if not regiao: break
            coordenada.x += regiao.x
            coordenada.y += regiao.y

        return extracoes

    def ler_imagem (self, imagem: Imagem) -> list[tuple[str, Coordenada, float]]:
        """Extrair informações da `imagem`
        - `for texto, coordenada, confianca in leitor.ler_imagem()`"""
        return self.__ler(imagem)

    def __ler (self, imagem: Imagem) -> list[tuple[str, Coordenada, float]]:
        """Receber a imagem e extrair os dados"""
        return [
            (texto, Coordenada.from_box((box[0][0], box[0][1], box[1][0], box[2][1])), confianca) # type: ignore
            for box, texto, confianca in self.__reader
                .readtext(imagem.pixels, mag_ratio=2, min_size=3, slope_ths=0.25, width_ths=0.4)
        ]

    def detectar_tela (self, regiao: Coordenada | None = None) -> list[Coordenada]:
        """Extrair coordenadas de textos da tela
        - `regiao` para limitar a área de extração"""
        imagem = capturar_tela(regiao, True)
        coordenadas = self.__detectar(imagem)

        # corrigir offset com a regiao informada
        for coordenada in coordenadas:
            if not regiao: break
            coordenada.x += regiao.x
            coordenada.y += regiao.y
    
        return coordenadas

    def detectar_imagem (self, imagem: Imagem) -> list[Coordenada]:
        """Extrair coordenadas da `imagem`"""
        return self.__detectar(imagem)

    def __detectar (self, imagem: Imagem) -> list[Coordenada]:
        """Receber a imagem e detectar as coordenadas"""
        boxes, _ = self.__reader.detect(imagem.pixels, mag_ratio=2, min_size=3, slope_ths=0.25, width_ths=0.4)
        boxes: list[tuple[np.int32, ...]] = np.concatenate(boxes) # type: ignore
        return [
            Coordenada.from_box((x1, y1, x2, y2)) # type: ignore
            for x1, x2, y1, y2 in boxes
        ]

    @staticmethod
    def encontrar_textos (textos: typing.Iterable[str],
                          extracao: list[tuple[str, Coordenada, float]]) -> list[Coordenada | None]:
        """Encontrar as coordenadas dos `textos` na `extraçao` retornada pela a leitura da tela
        - Resultado de retorno é na mesma ordem que `textos`
        - `None` caso não tenha sido encontrado o `texto`
        - Ordem dos métodos de procura
            1. exato
            2. normalizado exato
            3. similaridade entre textos
            4. similaridade entre textos levando em conta que o texto pode estar na `extraçao` concatenado com espaço com outro texto"""
        # copiar
        textos = list(textos)

        # 1 2 3
        coordenadas = [
            (util.encontrar_texto(texto, extracao, lambda item: item[0]) or (None, None))[1]
            for texto in textos
        ]
        if all(coordenadas) or all(c in coordenadas for _, c, _ in extracao):
            return coordenadas

        # --------------------------------------------------- #
        # 4 - Magia negra                                     #
        # Textos muito juntos podem ser concatenados pelo OCR #
        # --------------------------------------------------- #

        @functools.cache
        def gerar_combinacoes (texto: str, coordenada: Coordenada, quantidade=1) -> list[tuple[str, Coordenada]]:
            """Gerar combinações do `(texto, coordenada)` de acordo com a `quantidade` de palavras desejadas"""
            palavras, quantidade = texto.split(), max(1, quantidade)
            combinacoes_possiveis = len(palavras) - quantidade + 1
            largura_letra = coordenada.largura / (len(texto) or 1)

            combinacoes, offset_largura = [], 0.0
            for i in range(combinacoes_possiveis):
                palavra = " ".join(palavras[i : i + quantidade])
                c = Coordenada(
                    round(coordenada.x + offset_largura),
                    coordenada.y,
                    round(len(palavra) * largura_letra),
                    coordenada.altura
                )
                combinacoes.append((palavra, c))
                offset_largura += (1 + len(palavras[i])) * largura_letra

            return combinacoes

        # ordenar os textos decrescente para a palavra maior ter prioridade
        nao_encontrados = sorted(
            (index, textos[index])
            for index in range(len(textos))
            if not coordenadas[index] # já encontrado
        )
        nao_encontrados.sort(key=lambda item: item[1].lower(), reverse=True)

        for index, texto in nao_encontrados:
            qtd_palavras = len(texto.split(" "))
            # tentar encontrar um Match para o `texto` em `extração`
            for texto_extracao, coordenada, _ in extracao:
                if coordenada in coordenadas: continue # coordenada já está sendo utilizada
                if len(texto_extracao.split(" ")) <= 1: continue # desnecessário
                # checar Match
                combinacoes = gerar_combinacoes(texto_extracao, coordenada, qtd_palavras)
                _, coordenada = util.encontrar_texto(texto, combinacoes, lambda item: item[0]) or (None, None)
                if not coordenada or any(coordenada in c for c in coordenadas if c): continue # não encontrada ou sendo utilizada
                # inserir coordenada e finalizar procura do `texto` atual
                coordenadas[index] = coordenada
                break

        return coordenadas

__all__ = ["LeitorOCR"]