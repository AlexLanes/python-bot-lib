# std
import re, time, typing, difflib, unicodedata
# interno
from .. import tipagem

def aguardar_condicao (condicao: typing.Callable[[], bool | tipagem.SupportsBool],
                       timeout: int | float,
                       delay = 0.1) -> bool:
    """Repetir a função `condição` por `timeout` segundos até que resulte em `True`
    - Retorna um `bool` indicando se a `condição` foi atendida
    - Exceções são ignoradas"""
    tempo = cronometro()

    while tempo() < timeout:
        try:
            if condicao(): return True
        except Exception: pass
        time.sleep(delay)

    return False

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
                        key: typing.Callable[[T], str] | None = None) -> T | None:
    """Encontrar a melhor opção em `opções` onde igual ou parecido ao `texto`
    - `None` caso nenhuma opção gerou um resultado satisfatório
    - `key` pode ser informado uma função para apontar para a `str` caso `opções` não seja uma `list[str]`"""
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
    for chars, replace in [(r"[l1!]", "i"), (r"[0dq]", "o")]:
        texto_replace = re.sub(chars, replace, texto_replace)
        for index, texto in enumerate(textos_replace):
            textos_replace[index] = re.sub(chars, replace, texto)
    if texto_replace in textos_replace:
        return opcoes[textos_replace.index(texto_replace)]

    # comparando similaridade dos caracteres
    # algorítimo `gestalt pattern matching`
    def calcular_similaridade (a: str, b: str) -> float:
        # punir uma quantidade se tiver diferença no tamanho
        # ou punir bastante se for a mesma quantidade de caracteres
        punicao_tamanho = abs((len(a) - len(b)) * 0.05) or 0.15
        return difflib.SequenceMatcher(None, a, b).ratio() - punicao_tamanho

    similaridades = [calcular_similaridade(texto_normalizado, t) for t in textos_normalizados]
    maior = max(similaridades) if similaridades else 0
    return opcoes[similaridades.index(maior)] if maior >= 0.6 else None

def expandir_tempo (segundos: int | float) -> str:
    """Expandir a medida `segundos` para as duas primeiras unidades de grandeza
    - Hora, Minuto, Segundo ou Milissegundo"""
    if not segundos: return "0 segundos"
    tempos, segundos = [], round(segundos, 3)

    for nome, medida in [("hora", 60 ** 2), ("minuto", 60), ("segundo", 1), ("milissegundo", 0.001)]:
        if segundos < medida: continue
        tempos.append(f"{int(segundos / medida)} {nome}{"s" if segundos >= medida * 2 else ""}")
        segundos %= medida
        if len(tempos) == 2: break

    return " e ".join(tempos)

def transformar_tipo[T: tipagem.primitivo] (valor: str, tipo: type[T]) -> T:
    """Fazer a transformação do `valor` para `type(tipo)`
    - Função genérica"""
    match str(tipo):
        case "<class 'str'>": return valor
        case "<class 'int'>" | "<class 'float'>": return tipo(valor)
        case "<class 'bool'>": return valor.lower().strip() == "true"
        case _: return None

def cronometro (resetar=False) -> typing.Callable[[], float]:
    """Inicializa um cronômetro que retorna o tempo decorrido a cada chamada na função
    - `resetar` indicador para resetar o tempo após cada chamada
    - Arredondado para 3 casas decimais"""
    inicio = time.perf_counter()
    def func () -> float:
        nonlocal inicio
        agora = time.perf_counter()
        delta = round(agora - inicio, 3)        
        if resetar: inicio = agora
        return delta
    return func

__all__ = [
    "normalizar",
    "cronometro",
    "expandir_tempo",
    "encontrar_texto",
    "transformar_tipo",
    "aguardar_condicao",
    "remover_acentuacao"
]