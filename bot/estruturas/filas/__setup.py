# std
import bisect, typing
from collections import deque as Deque

class Stack [T]:
    """Last In First Out"""

    __dq: Deque[T]
    tamanho: int | None
    """Restrição de tamanho máximo dos elementos"""

    def __init__ (self, elementos: typing.Iterable[T] | None = None,
                        tamanho: int | None = None) -> None:
        """Inicializar o `Stack` com `tamanho` máximo opcional e adicionar `elementos` opcionalmente"""
        self.tamanho = None if not tamanho or tamanho < 0 else tamanho
        self.__dq = Deque(elementos or [], self.tamanho)

    def __len__ (self) -> int:
        """Quantidade de elementos"""
        return len(self.__dq)

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Stack[T] com {len(self)} elemento(s)>"

    def __str__ (self) -> str:
        return str([*self.__dq])

    def __iter__ (self) -> typing.Generator[T, None, None]:
        """Iteração sobre os elementos do Stack"""
        for elemento in self.__dq:
            yield elemento

    def __getitem__ (self, index: int) -> T:
        """Obter elemento no `index`"""
        return self.__dq[index]

    def __bool__ (self) -> bool:
        """Representação `bool` da classe"""
        return not self.empty()

    def empty (self) -> bool:
        """Indicador se o Stack está vazio"""
        return len(self) == 0

    def full (self) -> bool:
        """Indicador se o Stack chegou no tamanho máximo"""
        return len(self) == self.tamanho

    def push (self, elemento: T) -> bool:
        """Adicionar `elemento` no topo do Stack
        - Retorna indicador de sucesso devido a restrição do `tamanho`"""
        return False if self.full() else self.__dq.append(elemento) == None

    def peek (self) -> T:
        """Obter o elemento no topo sem remover do Stack
        - `IndexError` caso `self.empty()`"""
        return self[-1]

    def pop (self) -> T:
        """Obter o elemento no topo e remover do Stack
        - `IndexError` caso `self.empty()`"""
        return self.__dq.pop()

class Queue [T]:
    """Fist In First Out"""

    __dq: Deque[T]
    tamanho: int | None
    """Restrição de tamanho máximo dos elementos"""

    def __init__ (self, elementos: typing.Iterable[T] | None = None,
                        tamanho: int | None = None) -> None:
        """Inicializar a `Queue` com `tamanho` máximo opcional e adicionar `elementos` opcionalmente"""
        self.tamanho = None if not tamanho or tamanho < 0 else tamanho
        self.__dq = Deque(elementos or [], self.tamanho)

    def __len__ (self) -> int:
        """Quantidade de elementos"""
        return len(self.__dq)

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Queue[T] com {len(self)} elemento(s)>"

    def __str__ (self) -> str:
        return str([*self.__dq])

    def __iter__ (self) -> typing.Generator[T, None, None]:
        """Iteração sobre os elementos da Queue"""
        for elemento in self.__dq:
            yield elemento

    def __getitem__ (self, index: int) -> T:
        """Obter elemento no `index`"""
        return self.__dq[index]

    def __bool__ (self) -> bool:
        """Representação `bool` da classe"""
        return not self.empty()

    def empty (self) -> bool:
        """Indicador se a Queue está vazia"""
        return len(self) == 0

    def full (self) -> bool:
        """Indicador se a Queue chegou no tamanho máximo"""
        return len(self) == self.tamanho

    def add (self, elemento: T) -> bool:
        """Adicionar `elemento` na Queue
        - Retorna indicador de sucesso devido a restrição do `tamanho`"""
        return False if self.full() else self.__dq.append(elemento) == None

    def peek (self) -> T:
        """Obter o primeiro elemento sem remover da Queue
        - `IndexError` caso `self.empty()`"""
        return self[0]

    def poll (self) -> T:
        """Obter o primeiro elemento e remover da Queue
        - `IndexError` caso `self.empty()`"""
        return self.__dq.popleft()

class PriorityQueue [T]:
    """Queue com prioridade na ordem natural"""

    __dq: Deque[T]
    tamanho: int | None
    """Restrição de tamanho máximo dos elementos"""
    comparador: typing.Callable[[T], typing.Any]
    """Função para definir a prioridade
    - `Default` o item inteiro é utilizado"""

    def __init__ (self, elementos: typing.Iterable[T] | None = None,
                        tamanho: int | None = None,
                        comparador: typing.Callable[[T], typing.Any] | None = None) -> None:
        """Inicializar a `PriorityQueue` com `tamanho` máximo opcional e adicionar `elementos` opcionalmente"""
        self.tamanho = None if not tamanho or tamanho < 0 else tamanho
        self.comparador = comparador if comparador else lambda item: item
        self.__dq = Deque(
            sorted(elementos or [], key=self.comparador),
            self.tamanho
        )

    def __len__ (self) -> int:
        """Quantidade de elementos"""
        return len(self.__dq)

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<PriorityQueue[T] com {len(self)} elemento(s)>"

    def __str__ (self) -> str:
        return str([*self.__dq])

    def __iter__ (self) -> typing.Generator[T, None, None]:
        """Iteração sobre os elementos da PriorityQueue"""
        for elemento in self.__dq:
            yield elemento

    def __getitem__ (self, index: int) -> T:
        """Obter elemento no `index`"""
        return self.__dq[index]

    def __bool__ (self) -> bool:
        """Representação `bool` da classe"""
        return not self.empty()

    def empty (self) -> bool:
        """Indicador se a PriorityQueue está vazia"""
        return len(self) == 0

    def full (self) -> bool:
        """Indicador se a PriorityQueue chegou no tamanho máximo"""
        return len(self) == self.tamanho

    def add (self, elemento: T) -> bool:
        """Adicionar `elemento` na PriorityQueue
        - Retorna indicador de sucesso devido a restrição do `tamanho`"""
        if self.full(): return False
        return bisect.insort(self.__dq, elemento, key=self.comparador) == None

    def peek_low (self) -> T:
        """Obter o elemento com menor prioridade sem remover da PriorityQueue
        - `IndexError` caso `self.empty()`"""
        return self[0]

    def poll_low (self) -> T:
        """Obter o elemento com menor prioridade e remover da PriorityQueue
        - `IndexError` caso `self.empty()`"""
        return self.__dq.popleft()

    def peek_high (self) -> T:
        """Obter o elemento com maior prioridade sem remover da PriorityQueue
        - `IndexError` caso `self.empty()`"""
        return self[-1]

    def poll_high (self) -> T:
        """Obter o elemento com maior prioridade e remover da PriorityQueue
        - `IndexError` caso `self.empty()`"""
        return self.__dq.pop()

__all__ = [
    "Stack",
    "Queue",
    "Deque",
    "PriorityQueue"
]
