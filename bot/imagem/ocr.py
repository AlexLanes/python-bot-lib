# std
import typing, functools, warnings
# interno
from . import Coordenada, Imagem, capturar_tela
import bot
# externo
import numpy as np

warnings.filterwarnings("ignore", message="'pin_memory'")

class LeitorOCR:
    """Classe de abstração do pacote `EasyOCR` para ler/detectar textos em imagens
    #### [Documentação EasyOCR](https://www.jaided.ai/easyocr/documentation)
    - `linguagem` linguagens aceitas pelo `EasyOCR`. Default `en` que é mais preciso
    - `gpu=True` Caso possua GPU da NVIDIA, instalar o `CUDA Toolkit` e instalar as bibliotecas indicadas pelo [pytorch](https://pytorch.org/get-started/locally)
    - Possui alguns parâmetros customizáveis para alterar o leitor e detector

    ### Inicialização
    ```
    # Default utilizado a linguagem `en`, que é o mais otimizado, e sem `gpu`
    leitor = LeitorOCR()
    # O EasyOCR é custoso na inicialização
    # Utilizar sistema de cache ou constante para evitar ficar inicializando múltiplas vezes
    ```

    ### Parâmetros
    ```
    leitor.decoder      # Parâmetro utilizado pela decodificação de textos na leitura
    leitor.mag_ratio    # Taxa de ampliação da imagem
    leitor.min_size     # Filtrar caixas de texto menor que o valor mínimo em pixels
    leitor.slope_ths    # Filtrar caixas de texto menor que o valor mínimo em pixels
    leitor.width_ths    # Distância horizontal máxima para mesclar caixas
    leitor.allowlist    # Caracteres permitidos a serem retornados pelos métodos de leitura
    ```

    ### Detecção de Coordenadas de textos
    ```
    leitor.detectar_tela()              # Extrair coordenadas de textos da tela inteira
    leitor.detectar_tela(Coordenada)    # Extrair coordenadas de textos de parte da tela
    leitor.detectar_imagem(imagem)      # Extrair coordenadas da `imagem`
    ```

    ### Extração de textos
    ```
    leitor.ler_tela()                   # Extrair informações da tela inteira -> `(texto, coordenada, confiança)`
    leitor.ler_tela(Coordenada)         # Extrair informações de parte da tela -> `(texto, coordenada, confiança)`
    leitor.ler_imagem(imagem)           # Extrair informações da `imagem` -> `(texto, coordenada, confiança)`
    leitor.ler_texto_imagem(imagem)     # Ler e retornar os textos extraídos da `imagem` concatenados -> str

    # Extrair as colunas e linhas da `imagem` de uma tabela ()
    # Funciona apenas para tabelas com os nomes das colunas `left-align`
    leitor.ler_tabela(imagem)                               # Todas as colunas
    leitor.ler_tabela(imagem, ("Coluna1", "Coluna2", ...))  # Restringir colunas
    ```

    ### Útil
    ```
    # Concatenar as linhas da `extração` em uma só `str`
    leitor.concatenar_linhas(...)

    # Pode ser necessário pois o OCR não gera resultados 100% correto
    bot.util.encontrar_texto(...)   # Encontrar a melhor opção em `opções` onde igual ou parecido ao `texto`
    leitor.encontrar_textos(...)    # Encontrar as coordenadas dos `textos` na `extraçao` retornada pela a leitura da tela ou imagem
    ```
    """

    decoder: typing.Literal["greedy", "beamsearch"] = "greedy"
    """Parâmetro utilizado pela decodificação de textos na leitura
    - `greedy` rápido e simples mas pode errar mais
    - `beamsearch` mais lento porém melhor em precisão geral"""
    mag_ratio: int = 2
    """Taxa de ampliação da imagem"""
    min_size: int = 2
    """Filtrar caixas de texto menor que o valor mínimo em pixels"""
    slope_ths: float = 0.25
    """Inclinação máxima para ser considerado mesclar as caixas de texto"""
    width_ths: float = 0.4
    """Distância horizontal máxima para mesclar caixas
    - Diminuir o default `o.4` caso as `Coordenadas` estejam sendo mescladas"""
    allowlist: str | None = None
    """Caracteres permitidos a serem retornados pelos métodos de leitura
    - Default utilizado pelo modelo da linguagem"""

    def __init__ (self, *linguagem: str, gpu: bool = False) -> None:
        try: from easyocr import Reader
        except ImportError: raise ImportError("Pacote opcional [ocr] necessário. Realize `pip install bot[ocr]` para utilizar o LeitorOCR")
        self.reader = Reader(
            list(linguagem) or ["en"],
            gpu = gpu
        )

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

    def ler_texto_imagem (self, imagem: Imagem, concatenador: str = " ") -> str:
        """Ler e retornar os textos extraídos da `imagem` concatenados
        - É comparado a confiança do texto da `imagem`, `imagem.cinza()` e `imagem.binarizar()` e retornado a melhor"""
        dados = self.ler_imagem(imagem)
        confianca_dados = sum(confianca for _, _, confianca in dados)

        for modificador in (lambda: imagem.cinza(), lambda: imagem.binarizar()):
            dados_transformados = self.ler_imagem(modificador())
            confianca = sum(confianca for _, _, confianca in dados_transformados)
            if confianca < confianca_dados: continue
            confianca_dados = confianca
            dados = dados_transformados

        return concatenador.join(texto for texto, *_ in dados)

    def ler_tabela (self, imagem: Imagem,
                          nomes_colunas: typing.Iterable[str] | None = None,
                          margem_y_linhas: int = 5) -> list[dict[str, tuple[str, Coordenada]]]:
        """Extrair as colunas e linhas da `imagem` de uma tabela
        ### Limitação: Funciona apenas para tabelas com os nomes das colunas `left-align`
        - `nomes_colunas` limitar, renomear e buscar pelas colunas desejadas
        - `margem_y_linhas` para juntar linhas com a margem de erro `Y`
        - Diminiur `leitor.width_ths` caso os nomes das colunas estiverem sendo mesclados
        - Retornado as linhas sendo `{ nome_coluna: (texto_coluna, Coordenada do texto na `imagem`) }`"""
        tabela = list[dict[str, tuple[str, Coordenada]]]()
        largura_imagem = imagem.pixels.shape[1]

        # Detectar e agrupar as linhas da `imagem`
        linhas = list[list[Coordenada]]()
        for coordenada in self.__detectar(imagem):
            # Nova linha
            if not linhas or linhas[-1][0].y + margem_y_linhas <= coordenada.y:
                linhas.append([coordenada])
            # Mesma linha
            else: linhas[-1].append(coordenada)

        if not linhas: return tabela
        coordenada_headers, *coordenada_linhas = linhas

        # Corrigir a largura da coluna para ir até antes da próxima coluna
        for i, coordenada in enumerate(coordenada_headers):
            acrescimo_largura = coordenada_headers[i + 1].x if i < len(coordenada_headers) - 1 else largura_imagem
            coordenada.largura += acrescimo_largura - coordenada.x - coordenada.largura - 2

        # Extrair nome dos headers
        headers = {
            nome: coordenada
            for coordenada in coordenada_headers
            if (nome := self.ler_texto_imagem(imagem.recortar(coordenada)))
        }

        # Corrigir nome dos headers
        if nomes_colunas := list(nomes_colunas or []):
            headers_corrigido = {}
            nomes_headers = list(headers)
            for coluna in nomes_colunas:
                nome = bot.util.encontrar_texto(coluna, nomes_headers)
                assert nome, f"Coluna '{coluna}' não foi encontrada nos headers '{nomes_headers}'"
                nomes_headers.remove(nome)
                headers_corrigido[coluna] = headers[nome]
            headers = headers_corrigido

        # Extrair de cada linha os dados de acordo com os `headers`
        for coordenadas in coordenada_linhas:
            menor_y = min(coordenada.y for coordenada in coordenadas)
            maior_altura = max(coordenada.altura for coordenada in coordenadas)
            tabela.append({
                nome_header: (
                    self.ler_texto_imagem(imagem.recortar(coordenada)),
                    coordenada
                )
                for nome_header, coordenada_header in headers.items()
                if (coordenada := Coordenada(
                    x = coordenada_header.x,
                    y = menor_y,
                    largura = coordenada_header.largura,
                    altura = maior_altura,
                ))
            })

        return tabela

    def __ler (self, imagem: Imagem) -> list[tuple[str, Coordenada, float]]:
        """Receber a imagem e extrair os dados"""
        return [
            (texto, Coordenada.from_box((box[0][0], box[0][1], box[1][0], box[2][1])), confianca) # type: ignore
            for box, texto, confianca in self.reader.readtext(
                imagem.pixels,
                decoder   = self.decoder,
                mag_ratio = self.mag_ratio,
                min_size  = self.min_size,
                slope_ths = self.slope_ths,
                width_ths = self.width_ths,
                allowlist = self.allowlist,
            )
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
        boxes, _ = self.reader.detect(
            imagem.pixels,
            mag_ratio = self.mag_ratio,
            min_size  = self.min_size,
            slope_ths = self.slope_ths,
            width_ths = self.width_ths
        )
        boxes: list[tuple[np.int32, ...]] = np.concatenate(boxes) # type: ignore
        return [
            Coordenada.from_box((x1, y1, x2, y2)) # type: ignore
            for x1, x2, y1, y2 in boxes
        ]

    @staticmethod
    def encontrar_textos (textos: typing.Iterable[str],
                          extracao: list[tuple[str, Coordenada, float]]) -> list[Coordenada | None]:
        """Encontrar as coordenadas dos `textos` na `extraçao` retornada pela a leitura da tela ou imagem
        - Resultado de retorno é na mesma ordem que `textos`
        - `None` caso não tenha sido encontrado o `texto`
        - Ordem dos métodos de procura
            1. exato
            2. normalizado exato
            3. similaridade entre textos
            4. normalizado com replace de caracteres parecidos
            5. similaridade entre textos usando `difflib.SequenceMatcher`
            6. similaridade entre textos levando em conta que o texto pode estar na `extraçao` concatenado com espaço com outro texto"""
        # copiar
        textos = list(textos)

        # 1 2 3 4 5
        coordenadas = [
            (bot.util.encontrar_texto(texto, extracao, lambda item: item[0]) or (None, None))[1]
            for texto in textos
        ]
        if all(coordenadas) or all(c in coordenadas for _, c, _ in extracao):
            return coordenadas

        # --------------------------------------------------- #
        # 6 - Magia negra                                     #
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
                _, coordenada = bot.util.encontrar_texto(texto, combinacoes, lambda item: item[0]) or (None, None)
                if not coordenada or any(coordenada in c for c in coordenadas if c): continue # não encontrada ou sendo utilizada
                # inserir coordenada e finalizar procura do `texto` atual
                coordenadas[index] = coordenada
                break

        return coordenadas

    @staticmethod
    def concatenar_linhas (extracao: list[tuple[str, Coordenada, float]],
                           margem_y: int = 5) -> list[tuple[str, int]]:
        """Concatenar as linhas da `extração` em uma só `str`
        - `margem_y` para juntar linhas com a margem de erro `Y`
        - Retornado uma lista das linhas sendo `(linha, Y central da linha)`"""
        linhas = list[tuple[list[str], int]]()

        for texto, coordenada, _ in extracao:
            centro_y = coordenada.y + coordenada.altura // 2
            # Nova linha
            if not linhas or linhas[-1][1] + margem_y <= centro_y:
                linhas.append(([texto], centro_y))
            # Mesma linha
            else: linhas[-1][0].append(texto)

        return [
            (" ".join(textos), centro_y)
            for textos, centro_y in linhas
        ]

__all__ = ["LeitorOCR"]