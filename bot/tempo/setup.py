# std
import time
# interno
from bot.tempo.cronometro import Cronometro

def sleep (segundos: int | float = 1) -> None:
    """Sleep tradicional com padrão de `1 segundo`"""
    time.sleep(segundos)

def formatar_tempo_decorrido (segundos: int | float | Cronometro) -> str:
    """Formatar a medida `segundos` para as duas maiores unidades de grandeza
    - Hora
    - Minuto
    - Segundo
    - Milissegundo"""
    assert segundos >= 0, "Segundos não deve ser negativo"

    if isinstance(segundos, Cronometro):
        segundos = segundos.tempo_decorrido
    if not segundos: return "0 segundos"

    tempos, segundos = [], round(segundos, 3)
    for nome, medida in [("hora", 60 ** 2), ("minuto", 60), ("segundo", 1), ("milissegundo", 0.001)]:
        if segundos < medida: continue
        tempos.append(f"{int(segundos / medida)} {nome}{"s" if segundos >= medida * 2 else ""}")
        segundos %= medida
        if len(tempos) == 2: break

    return " e ".join(tempos)

__all__ = [
    "sleep",
    "Cronometro",
    "formatar_tempo_decorrido",
]