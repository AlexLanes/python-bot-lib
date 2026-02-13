# std
import re, typing, difflib, unicodedata
# interno
import bot

def remover_acentuacao (string: str) -> str:
    """Remover acentuações da `string`"""
    nfkd = unicodedata.normalize("NFKD", str(string))
    ascii = nfkd.encode("ASCII", "ignore")
    return ascii.decode("utf-8", "ignore")

def normalizar (string: str) -> str:
    """Strip, lower, replace espaços por underline, remoção de acentuação e remoção de caracteres != `a-zA-Z0-9_`"""
    string = re.sub(r"\s+", "_", string.strip().lower())
    string = remover_acentuacao(string)
    return re.sub(r"\W", "", string).replace("__", "_")

def encontrar_texto[T] (texto: str,
                        opcoes: typing.Iterable[T],
                        key: typing.Callable[[T], str] | None = None,
                        similaridade_minima: float = 0.75) -> T | None:
    """Encontrar a melhor opção em `opções` onde igual ou parecido ao `texto`
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
    textos = [key_to_text(opcao) for opcao in opcoes]

    # opção exata
    if texto in textos:
        return opcoes[textos.index(texto)]

    # opção normalizada
    texto_normalizado = normalizar(texto)
    textos_normalizados = [normalizar(opcao) for opcao in textos]
    if texto_normalizado in textos_normalizados:
        return opcoes[textos_normalizados.index(texto_normalizado)]

    # opção normalizada com replace de caracteres parecidos
    texto_replace = texto_normalizado
    textos_replace = textos_normalizados.copy()
    for chars, replace in [("[l1!]", "i"), ("[0dq]", "o"), ("rn", "m")]:
        texto_replace = re.sub(chars, replace, texto_replace)
        for index, texto in enumerate(textos_replace):
            textos_replace[index] = re.sub(chars, replace, texto)
    if texto_replace in textos_replace:
        return opcoes[textos_replace.index(texto_replace)]

    # comparando similaridade dos caracteres
    # algorítimo `gestalt pattern matching`
    # punir uma quantidade se tiver diferença no tamanho
    def calcular_similaridade (a: str, b: str) -> float:
        punicao_tamanho = abs((len(a) - len(b)) * 0.1)
        return difflib.SequenceMatcher(None, a, b).ratio() - punicao_tamanho

    similaridades = [calcular_similaridade(texto_normalizado, t) for t in textos_normalizados]
    maior = max(similaridades) if similaridades else 0
    return opcoes[similaridades.index(maior)] if maior >= similaridade_minima else None

def transformar_tipo[T: bot.tipagem.primitivo] (valor: str, tipo: type[T]) -> T:
    """Fazer a transformação do `valor` para `type(tipo)`
    - Função genérica"""
    match tipo():
        case bool():    return valor.lower().strip() == "true" # type: ignore
        case float():   return float(valor) # type: ignore
        case int():     return int(valor) # type: ignore
        case _:         return valor # type: ignore

__all__ = [
    "normalizar",
    "encontrar_texto",
    "transformar_tipo",
    "remover_acentuacao"
]