# std
from __future__ import annotations
import typing, dataclasses
import itertools, functools
# interno
import bot

class ICursorPEP249 (typing.Protocol):
    @property
    def rowcount (self) -> int | None: ...
    @property
    def description (self) -> typing.Iterable[typing.Sequence[typing.Any]] | None: ...
    def __iter__ (self) -> typing.Self: ...
    def __next__ (self) -> typing.Sequence[typing.Any]: ...
    def close (self) -> None: ...

@dataclasses.dataclass
class ResultadoSQL:
    """Classe utilizada no retorno ao executar comando em banco de dados

    ### Representação
    ```
    - repr(resultado)
    - resultado.linhas_afetadas == None # não aplicado para o comando
    - resultado.colunas e resultado.linhas # para comandos de consulta
    ```

    ### Indicador se teve linhas_afetadas ou linhas retornadas
    ```
    - bool(resultado)
    - if resultado: ...
    ```

    ### Quantidade de linhas retornadas
    ```
    - len(resultado)
    - resultado.quantidade_linhas
    ```

    ### Iteração sobre as linhas retornadas
    ```
    # As linhas são consumidas quando iteradas sobre
    - linha: tuple[tipagem.tipoSQL, ...] = next(resultado.linhas)
    - for linha in resultado.linhas: ...
    - for linha in resultado: ...
    ```

    ### Transformações das linhas retornadas
    ```
    - resultado.primeira_linha
    - resultado.to_dict()
    - resultado.unmarshal(classe)
    - resultado.filtrar(lambda linha: bool)
    - resultado.transformar(nome_coluna = lambda valor: str(valor), ...)
    ```
    """

    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica ao comando sql"""
    colunas: tuple[str, ...]
    """Colunas das linhas retornadas (se houver)"""
    linhas: typing.Iterable[tuple[bot.tipagem.tipoSQL, ...]]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    cursor: ICursorPEP249 | None = None
    """Cursor de onde os dados são obtidos
    - Fechado automaticamente caso informado"""

    @classmethod
    def from_cursor (cls, cursor: ICursorPEP249) -> ResultadoSQL:
        colunas = tuple(str(coluna) for coluna, *_ in cursor.description) if cursor.description else tuple()
        return cls(
            None if cursor.rowcount is None else max(cursor.rowcount, 0),
            colunas,
            (tuple(linha) for linha in cursor) if colunas else tuple(),
            cursor
        )

    @functools.cached_property
    def quantidade_linhas (self) -> int:
        """Obter a quantidade de linhas retornadas sem consumir o gerador"""
        self.linhas, linhas = itertools.tee(self.linhas)
        return sum(1 for _ in linhas)

    @functools.cached_property
    def primeira_linha (self) -> dict[str, bot.tipagem.tipoSQL]:
        """Cache da primeira linha no resultado
        - Não altera o gerador das `linhas`"""
        self.linhas, linhas = itertools.tee(self.linhas)
        try: return dict(zip(self.colunas, next(linhas)))
        except StopIteration: return {}

    def __del__ (self) -> None:
        if self.cursor is None: return
        try: self.cursor.close()
        except Exception: pass

    def __iter__ (self) -> typing.Generator[tuple[bot.tipagem.tipoSQL, ...], None, None]:
        """Generator do `self.linhas`"""
        for linha in self.linhas:
            yield linha

    def __repr__ (self) -> str:
        "Representação da classe"
        linhas_afetadas = self.linhas_afetadas
        quantidade_linhas = self.quantidade_linhas
        return f"<ResultadoSQL {linhas_afetadas=!r} {quantidade_linhas=!r}>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return ((self.linhas_afetadas or 0) >= 1) or bool(self.quantidade_linhas)

    def __len__ (self) -> int:
        return self.quantidade_linhas

    def transformar (self, **colunas: typing.Callable[[bot.tipagem.tipoSQL], typing.Any]) -> typing.Self:
        """Aplicar uma transformação no valor das colunas informadas
        - `resultado.transformar(nome_coluna = lambda valor: str(valor), ...)`"""
        linhas = self.linhas
        transformacoes = bot.estruturas.DictNormalizado(colunas)
        self.linhas = (
            tuple(
                transformacoes[coluna](valor) if coluna in transformacoes else valor
                for coluna, valor in zip(map(str.lower, self.colunas), linha)
            )
            for linha in linhas
        )
        return self

    def filtrar (self, filtro: typing.Callable[[tuple[bot.tipagem.tipoSQL, ...]], bot.tipagem.SupportsBool]) -> typing.Self:
        """Aplicar um filtro nas linhas retornadas
        - `resultado.filtrar(lambda linha: bool)`"""
        linhas = self.linhas
        self.linhas = (
            linha
            for linha in linhas
            if bool(bot.estruturas.Resultado(filtro, linha).valor_ou(False))
        )
        return self

    def to_dict (self) -> list[dict[str, bot.tipagem.tipoSQL]]:
        """Representação das linhas e colunas no formato `dict`
        - Consome o gerador das `linhas`"""
        return [
            dict(zip(self.colunas, linha))
            for linha in self
        ]

    def stringify (self, indentar: bool = False) -> str:
        """Representação das linhas e colunas no formato `json str`
        - Consome o gerador das `linhas`"""
        return bot.formatos.Json(self.to_dict()).stringify(indentar)

    def unmarshal[T] (self, cls: type[T]) -> list[T]:
        """Realizar o unmarshal das linhas conforme a classe anotada `cls`
        - Consome o gerador das `linhas`"""
        return (
            bot.formatos.Unmarshaller(cls)
            .parse(self.to_dict())
        )

__all__ = ["ResultadoSQL"]