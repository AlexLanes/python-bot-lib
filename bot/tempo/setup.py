# std
import time
from datetime import (
    datetime  as Datetime,
    timezone  as Timezone,
    timedelta as Timedelta
)
# interno
from bot.tempo.cronometro import Cronometro

TIMEZONE_BRT = Timezone(Timedelta(hours=-3))

def sleep (segundos: int | float = 1) -> None:
    """Sleep tradicional com padrão de `1 segundo`"""
    time.sleep(segundos)

def formatar_tempo_decorrido (segundos: int | float | Cronometro) -> str:
    """Formatar a medida `segundos` para as duas maiores unidades de grandeza
    - Horas
    - Minutos
    - Segundos
    - Milissegundos"""
    assert segundos >= 0, "Segundos não deve ser negativo"

    if isinstance(segundos, Cronometro):
        segundos = segundos.decorrido
    if not segundos: return "0 segundos"

    tempos, segundos = [], round(segundos, 3)
    for nome, medida in [("hora", 60 ** 2), ("minuto", 60), ("segundo", 1), ("milissegundo", 0.001)]:
        if segundos < medida: continue
        tempos.append(f"{int(segundos / medida)} {nome}{"s" if segundos >= medida * 2 else ""}")
        segundos %= medida
        if len(tempos) == 2: break

    return " e ".join(tempos)

def datetime_brt (com_timezone: bool = False) -> Datetime:
    """Obter o `Datetime` no Timezone `BRT`
    - `com_timezone` para remover a informação do offset no `Datetime`"""
    data = Datetime.now(TIMEZONE_BRT)
    return data if com_timezone else data.replace(tzinfo=None)

def datetime_utc (com_timezone: bool = False) -> Datetime:
    """Obter o `Datetime` no Timezone `UTC`
    - `com_timezone` para remover a informação do offset no `Datetime`"""
    data = Datetime.now(Timezone.utc)
    return data if com_timezone else data.replace(tzinfo=None)

__all__ = [
    "sleep",
    "Cronometro",
    "TIMEZONE_BRT",
    "datetime_brt",
    "datetime_utc",
    "formatar_tempo_decorrido",
]