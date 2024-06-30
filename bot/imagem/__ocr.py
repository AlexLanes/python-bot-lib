# std
from typing import Iterable
from functools import cache
# interno
from ..estruturas import Coordenada
from .. import util, logger, tipagem
from .__setup import capturar_tela, transformar_pillow
# externo
import numpy as np
from PIL import Image

class LeitorOCR:
    """Classe de abstração do EasyOCR
    - Caso possua GPU da NVIDIA, instalar o `CUDA Toolkit` e instalar as bibliotecas indicadas pelo pytorch https://pytorch.org/get-started/locally/"""

    def __init__ (self, confianca: tipagem.PORCENTAGENS = "0.4"):
        """Inicia o leitor OCR
        - `confianca` porcentagem mínima de confiança no texto extraído `(entre 0.0 e 1.0)`"""
        try: from easyocr import Reader
        except ImportError: raise ImportError("Instale o bot com o parâmetro opcional [ocr] para utulizar o LeitorOCR")
        self.__reader = Reader(["en"])
        self.__confianca = max(0.0, min(1.0, float(confianca)))

    def ler_tela (self, regiao: Coordenada = None) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas da tela na posição `coordenada` 
        - `regiao` vazia para ler a tela inteira
        - `for texto, coordenada in leitor.ler_tela()`"""
        cronometro = util.cronometro()
        extracoes = self.__ler(capturar_tela(regiao, True))

        # corrigir offset com a regiao informada
        for _, coordenada in extracoes:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y

        tempo = util.expandir_tempo(cronometro())
        logger.debug(f"Leitura da tela realizada em {tempo}")
        return extracoes

    def ler_imagem (self, imagem: tipagem.imagem) -> list[tuple[str, Coordenada]]:
        """Extrair texto e coordenadas de uma imagem
        - `for texto, coordenada in leitor.ler_imagem()`"""
        cronometro = util.cronometro()
        extracoes = self.__ler(transformar_pillow(imagem))
        tempo = util.expandir_tempo(cronometro())
        logger.debug(f"Leitura da imagem realizada em {tempo}")
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
        cronometro = util.cronometro()
        coordenadas = self.__detectar(capturar_tela(regiao, True))

        # corrigir offset com a regiao informada
        for coordenada in coordenadas:
            if not regiao: break # região não foi informada, não há o que corrigir
            coordenada.x += regiao.x
            coordenada.y += regiao.y
    
        tempo = util.expandir_tempo(cronometro())
        logger.debug(f"Tela detectada em {tempo}")
        return coordenadas

    def detectar_imagem (self, imagem: tipagem.imagem) -> list[Coordenada]:
        """Extrair coordenadas de uma imagem
        - `confiança` não se aplica na detecção"""
        cronometro = util.cronometro()
        coordenadas = self.__detectar(transformar_pillow(imagem))
        tempo = util.expandir_tempo(cronometro())
        logger.debug(f"Imagem detectada em {tempo}")
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

    @staticmethod
    def encontrar_textos (textos: Iterable[str], extracao: list[tuple[str, Coordenada]]) -> list[Coordenada | None]:
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
        if all(coordenadas) or all(c in coordenadas for _, c in extracao):
            return coordenadas

        # --------------------------------------------------- #
        # 4 - Magia negra                                     #
        # Textos muito juntos podem ser concatenados pelo OCR #
        # --------------------------------------------------- #

        @cache
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
            for texto_extracao, coordenada in extracao:
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
