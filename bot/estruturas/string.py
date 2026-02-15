# std
from __future__ import annotations
import re, typing, difflib, unicodedata

class String (str):
    """Extensão da classe nativa `str` com utilitários adicionais,
    principalmente para operações com expressões regulares e
    normalização de texto.

    A classe preserva todos os comportamentos de `str`, retornando
    sempre instâncias de `String` nos métodos adicionados, permitindo
    encadeamento nas chamadas."""

    def __repr__ (self) -> str:
        return f"<String '{str(self)}'>"

    RE_MULTILINE = re.MULTILINE
    RE_IGNORECASE = re.IGNORECASE
    PATTERN_NOTWORD = re.compile(r"\W")
    PATTERN_ESPACOS = re.compile(r"\s+")
    PATTERN_UNDERLINES = re.compile(r"_+")

    @staticmethod
    def pattern (pattern: str, flags: re.RegexFlag = re.NOFLAG) -> re.Pattern[str]:
        """Criar um `Pattern` regex com as devidas `flags`
        - `flags` algumas como constante em `String`. Concatenar com `|` caso queira + de 1
        - Mais eficiente caso queira utilizar várias vezes"""
        return re.compile(pattern, flags)

    def re_replace (self, pattern: str | re.Pattern[str],
                          replacement: str,
                          count: int = 0) -> String:
        """Replace com regex começando da esquerda até `count` vezes
        - `pattern` pode ser uma string normal ou regex pré-compilado obtido pelo `String.pattern()`
        - `count=0` sem restrição"""
        return String(re.sub(pattern, replacement, self, count))

    def re_fullmatch (self, pattern: str | re.Pattern[str]) -> bool:
        """Checar se o `pattern` informado corresponde com o começo ao fim da `String`"""
        return bool(re.fullmatch(pattern, self))

    def re_search (self, pattern: str | re.Pattern[str]) -> String | None:
        """Procurar em alguma posição da `String` o primeiro `pattern` informado
        - `None` caso não tenha sido encontrado"""
        match = re.search(pattern, self)
        return String(match.group()) if match else None

    def re_search_n (self, pattern: str | re.Pattern[str]) -> list[String]:
        """Procurar em todas as posições da `String` o `pattern` informado"""
        return [
            String(match.group())
            for match in re.finditer(pattern, self)
        ]

    def remover_acentuacao (self) -> String:
        """Remover acentuações"""
        nfkd = unicodedata.normalize("NFKD", self)
        ascii = nfkd.encode("ASCII", "ignore")
        return String(ascii.decode("utf-8", "ignore"))

    def normalizar (self) -> String:
        """Strip, lower, replace espaços por underline, remoção de acentuação e remoção de caracteres `!=` `a-zA-Z0-9_`"""
        return (
            String(self.strip().lower())
            .remover_acentuacao()
            .re_replace(self.PATTERN_ESPACOS, "_")
            .re_replace(self.PATTERN_NOTWORD, "")
            .re_replace(self.PATTERN_UNDERLINES, "_")
        )

    def encontrar_texto[T] (self, opcoes: typing.Iterable[T],
                                  key: typing.Callable[[T], str] | None = None,
                                  similaridade_minima: float = 0.75) -> T | None:
        """Encontrar a melhor opção em `opções` onde igual ou parecido a `String`. Útil para `OCR` com cenários sem exatidão.
        - `None` caso nenhuma opção gerou um resultado satisfatório
        - `key` pode ser informado uma função para apontar para a `str` caso `opções` não seja uma `list[str]`
        - Ordem dos métodos de procura
            1. exato
            2. normalizado exato
            3. normalizado com replace de caracteres parecidos
            4. similaridade entre textos usando `difflib.SequenceMatcher` com o valor `similaridade_minima`
                - `similaridade_minima` entre 0.0 e 1.0
                - `similaridade_minima=0` para desativar"""
        opcoes = list(opcoes)
        key_to_text = key or (lambda opcao: opcao)
        textos = list[str](key_to_text(opcao) for opcao in opcoes)

        # 1. opção exata
        if self in textos:
            return opcoes[textos.index(self)]

        # 2. opção normalizada
        texto_normalizado = self.normalizar()
        textos_normalizados = [String(opcao).normalizar() for opcao in textos]
        if texto_normalizado in textos_normalizados:
            return opcoes[textos_normalizados.index(texto_normalizado)]

        # 3. opção normalizada com replace de caracteres parecidos
        texto_replace, textos_replace = texto_normalizado, textos_normalizados.copy()
        for pattern, replacement in [("[l1!]", "i"), ("[0dq]", "o"), ("rn", "m")]:
            texto_replace = texto_replace.re_replace(pattern, replacement)
            textos_replace = [texto.re_replace(pattern, replacement) for texto in textos_replace]
        if texto_replace in textos_replace:
            return opcoes[textos_replace.index(texto_replace)]

        # 4. comparando similaridade dos caracteres
        # algorítimo `gestalt pattern matching`
        # punir uma quantidade se tiver diferença no tamanho
        if not similaridade_minima: return
        def calcular_similaridade (a: str, b: str) -> float:
            punicao_tamanho = abs((len(a) - len(b)) * 0.1)
            return difflib.SequenceMatcher(None, a, b).ratio() - punicao_tamanho

        similaridades = [calcular_similaridade(texto_normalizado, t) for t in textos_normalizados]
        maior = max(similaridades) if similaridades else 0
        return opcoes[similaridades.index(maior)] if maior >= similaridade_minima else None
