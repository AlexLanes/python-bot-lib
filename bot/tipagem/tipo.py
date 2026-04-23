# std
from __future__ import annotations
import inspect, functools, operator
from types import UnionType
from typing import (
    Any, Literal, Union,
    TypeAliasType, TypeVar,
    get_args, get_origin, get_type_hints
)
# interno
from bot.tipagem import primitivo

class Tipo[T: type | UnionType]:
    """Classe com métodos úteis para obter informações de um `type` e realizar comparações"""

    t: T
    """Tipo absoluto sem `TypeAlias` podendo ser um `UnionType` ou qualquer outro tipo, inclusive o `Any`"""

    def __init__ (self, t: T | TypeAliasType) -> None:
        # Remover `TypeVar` [T]
        t = t.__bound__ or Any if isinstance(t, TypeVar) else t

        # Remover `TypeAlias`
        i = 0
        while isinstance(t, TypeAliasType) and i < 10:
            t = t.__value__
            i += 1

        # Transformar `Union` em `UnionType`
        if get_origin(t) is Union:
            t = functools.reduce(operator.or_, (
                tipo.t
                for tipo in map(Tipo, get_args(t))
            ))

        # Flatten de `UnionType | Union` dentro de `UnionType`
        if isinstance(t, UnionType):
            itens: list[type] = []
            for arg in t.__args__:
                arg = Tipo(arg).t
                if isinstance(arg, UnionType):
                    itens.extend(arg.__args__)
                else: itens.append(arg)
            t = functools.reduce(operator.or_, itens)

        self.t = t # type: ignore

    def __repr__ (self) -> str:
        return f"Tipo[{self.t}]"

    @classmethod
    def Any (cls) -> Tipo[type]:
        """Criar um `Tipo[Any]`"""
        return Tipo(Any) # type: ignore

    @classmethod
    def from_value (cls, value: object) -> Tipo[type]:
        return Tipo(type(value))

    @functools.cached_property
    def origin (self) -> type | UnionType:
        """Classe originária sem os genéricos ou uniões"""
        return get_origin(self.t) or self.t

    @property
    def args (self) -> tuple[Any, ...]:
        """Argumentos presentes nos genéricos ou uniões"""
        return get_args(self.t)

    @functools.cached_property
    def args_as_tipo (self) -> tuple[Tipo[type], ...]:
        """Argumentos presentes nos genéricos ou uniões transformados em `Tipo`
        - Não usar me `Literal`"""
        return tuple(map(Tipo, self.args))

    @property
    def as_union (self) -> Tipo[UnionType]:
        """Obter o tipo como `UnionType`
        - Necessário testar `self.is_union()` antes
        - `AssertionError` caso seja `type`"""
        assert isinstance(self.t, UnionType), f"{self} é um type e não uma União"
        return Tipo(self.t)

    def is_union (self) -> bool:
        """Checar se o tipo é um `UnionType` de n tipos"""
        return isinstance(self.t, UnionType)

    @property
    def as_type (self) -> Tipo[type]:
        """Obter o tipo como `type`
        - Necessário testar `self.is_type()` antes
        - `AssertionError` caso seja `UnionType`"""
        assert not isinstance(self.t, UnionType), f"{self} é uma União e não um type"
        return Tipo(self.t)

    def is_type (self) -> bool:
        """Checar se o tipo não é um `UnionType`"""
        return not self.is_union()

    def is_any (self) -> bool:
        """Checar se o tipo é `Any`"""
        return self.origin is Any

    def is_literal (self) -> bool:
        """Checar se o tipo é um `Literal`"""
        return self.origin is Literal

    def is_class (self) -> bool:
        """Checar se o tipo é uma `class`
        - Ignora classes dos `builtins`"""
        return (
            self.t.__module__ != "builtins"
            and self.is_type()
            and self.origin not in (Any, Literal)
            and inspect.isclass(self.origin)
        )

    def is_primitivo (self) -> bool:
        """Checar se o tipo é `primitivo`
        - `UnionType == False`"""
        return (
            self.origin_in_union(primitivo)
            if self.is_type()
            else False
        )

    def origin_in (self, *tipos: type | TypeAliasType) -> bool:
        """Checar se a origem do tipo é algum dos `tipos` informados"""
        return any(
            self.origin is tipo.origin
            for tipo in map(Tipo, tipos)
        )

    def origin_in_union (self, union: UnionType | TypeAliasType) -> bool:
        """Checar se a origem do tipo é algum entre a `union`"""
        return any(
            self.origin is tipo.origin
            for tipo in Tipo(union).args_as_tipo
        )

    def annotations (self) -> dict[str, Tipo[type | UnionType]]:
        """Coletar as anotações do tipo, considerando que é uma `class`
        - Obtém as propriedades anotadas da classe base e seus parentes
        - Retorna `{ nome_propriedade: Tipo(tipo_propriedade) }`"""
        anotacoes = dict[str, Tipo[type | UnionType]]()

        if isinstance(self.origin, UnionType):
            return anotacoes

        for cls in reversed(self.origin.__mro__):
            try: hints = get_type_hints(cls, include_extras=True)
            except Exception: hints = getattr(cls, '__annotations__', {})
            anotacoes.update({
                str(nome): Tipo(tipo)
                for nome, tipo in hints.items()
            })

        return anotacoes

    def isinstance (self, valor: Any) -> bool:
        """Checar se o `valor` é instância do tipo de origem
        - `Any == True`
        - `Literal` o `valor` deve estar nos `args`
        - `UnionType` o `valor` deve ser a instância de algum dos `args`"""
        # Any
        if self.is_any():
            return True

        # Literal
        if self.is_literal():
            return valor in self.args

        # UnionType
        if self.is_union():
            return any(
                t.isinstance(valor)
                for t in self.args_as_tipo
            )

        # type
        try: return isinstance(valor, self.origin)
        except Exception: return False

    def validar[V] (self, valor: V, **kwargs: str) -> V:
        """Validar se o `valor` está de acordo com o tipo e retornar o `valor`
        - Erro caso o `valor` não possua o tipo esperado
        - Tipos Esperados:
            - `(str, int, float, bool, None)`
            - `dict`
            - `list`
            - `Any`
            - `Literal`
            - `|` `Union`
        """
        # Any | Literal | Primitivo
        if (self.is_any() or self.is_literal() or self.is_primitivo()) and self.isinstance(valor):
            return valor

        # Union
        caminho = kwargs.get("caminho", "$")
        if self.is_union():
            for tipo in self.args_as_tipo:
                try: return tipo.validar(valor, caminho=caminho)
                except Exception: pass

        # List
        if self.origin_in(list) and isinstance(valor, list):
            tipo, *_ = self.args_as_tipo or (self.Any(),)
            for i, item in enumerate(valor):
                tipo.validar(item, caminho=f"{caminho}[{i}]")
            return valor

        # Dict
        if self.origin_in(dict) and isinstance(valor, dict):
            key, value = self.args_as_tipo or (self.Any(), self.Any())
            for k, v in valor.items():
                key.validar(k, caminho=f"{caminho}[{k!r}]")
                value.validar(v, caminho=f"{caminho}[{k!r}]")
            return valor

        raise Exception(
            f"Erro ao validar um valor para o {self}; "
            f"Caminho({caminho}); "
            f"Encontrado({type(valor)}) Valor({valor})"
        )

__all__ = ["Tipo"]