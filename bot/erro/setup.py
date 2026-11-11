# std
from __future__ import annotations
import time, types, typing, functools
# interno
import bot

P = typing.ParamSpec("P")

def retry[R] (
        *erros: type[Exception],
        tentativas: int = 3,
        segundos: int | float = 0.0,
        ignorar: tuple[type[Exception], ...] = (NotImplementedError,),
        on_error: typing.Callable[[tuple[typing.Any, ...], dict[str, typing.Any]], typing.Any] | None = None
    ) -> typing.Callable[[typing.Callable[P, R]], typing.Callable[P, R]]: # type: ignore
    """Realizar `tentativas` de se chamar uma função após algum dos `erros` e aguardar `segundos` até tentar novamente
    - Usar como decorador em uma função `@`
    - `erros` especificar as exceções permitidas para retry. `(Default: Exception)`
    - `ignorar` exceções para não se aplicar o retry. `(Default: NotImplementedError)`
    - `on_error` uma função para ser executada após um erro.
        - Aceita 2 parâmetros `args, kwargs` com os argumentos que foram informados na chamada da função
    - `raise` na última tentativa com falha"""
    assert tentativas >= 1 and segundos >= 0.0, "O @retry espera tentativas >= 1 e segundos >= 0.0"
    erros = erros or (Exception,)

    def retry (func: typing.Callable[P, R]) -> typing.Callable[P, R]:
        nome_funcao = func.__name__

        @functools.wraps(func)
        def wrapper (*args: P.args, **kwargs: P.kwargs) -> R:
            for tentativa in range(1, tentativas + 1):
                try: return func(*args, **kwargs)

                except *ignorar as grupo_ignorado:
                    try: on_error(args, kwargs) if on_error else None
                    except Exception: pass
                    excecao = grupo_ignorado.exceptions[-1]
                    nome_excecao = type(excecao).__name__
                    excecao.add_note(f"Função({nome_funcao}) apresentou erro ao ser executada; Exceção '{nome_excecao}' não permitida a retentativa")
                    raise

                except *erros as grupo_excecoes:
                    try: on_error(args, kwargs) if on_error else None
                    except Exception: pass

                    excecao = grupo_excecoes.exceptions[-1]
                    bot.logger.alertar(
                        f"Tentativa {tentativa}/{tentativas} de execução da função({nome_funcao}) resultou em erro",
                        tipo_erro = type(excecao).__name__,
                        mensagem_erro = str(excecao).strip()
                    )
                    if tentativa < tentativas: time.sleep(segundos)
                    else:
                        excecao.add_note(f"Foram realizadas {tentativas} tentativa(s) de execução da função({nome_funcao})")
                        raise excecao

            # nunca
            raise

        return wrapper
    return retry

def adicionar_prefixo[R] (
        prefixo: str | typing.Callable[[tuple[typing.Any, ...], dict[str, typing.Any]], str]
    ) -> typing.Callable[[typing.Callable[P, R]], typing.Callable[P, R]]: # type: ignore
    """Adicionar uma mensagem de prefixo no erro, caso a função resulte em `Exception`
    - Usar como decorador em uma função `@`
    - Prefixo pode ser um `str` ou um `lambda args, kwargs: ""` para capturar os argumentos da função"""
    def prefixar_erro (func: typing.Callable[P, R]) -> typing.Callable[P, R]:

        @functools.wraps(func)
        def wrapper (*args: P.args, **kwargs: P.kwargs) -> R:
            try: return func(*args, **kwargs)
            except Exception as erro:
                tipo_excecao = type(erro)
                msg_erro = str(erro)
                msg_prefixo = prefixo(args, kwargs) if callable(prefixo) else prefixo
                mensagem_prefixada = msg_erro if msg_erro.startswith(msg_prefixo) else f"{msg_prefixo}; {msg_erro}"
                raise tipo_excecao(mensagem_prefixada, *erro.args[1 :]).with_traceback(erro.__traceback__) from None

        return wrapper
    return prefixar_erro

def adicionar_prefixo_classe[R] (prefixo: str) -> typing.Callable[[R], R]:
    """Adicionar uma mensagem de prefixo no erro, caso algum item interno da classe resulte em `Exception`
    - Usar como decorador em uma classe `@`
    - `__init__, métodos, @property, @staticmethod e @classmethod`"""
    def getattribute_alterado (self: R, name: str, /) -> typing.Any:
        try: valor = object.__getattribute__(self, name)
        except Exception as erro:
            tipo_excecao = type(erro)
            msg_erro = str(erro)
            mensagem_prefixada = msg_erro if msg_erro.startswith(prefixo) else f"{prefixo}; {msg_erro}"
            raise tipo_excecao(mensagem_prefixada, *erro.args[1 :]).with_traceback(erro.__traceback__) from None
        return valor if not isinstance(valor, types.MethodType) else adicionar_prefixo(prefixo)(valor)

    def prefixar_erro_classe (cls: R) -> R:
        cls.__getattribute__ = getattribute_alterado # type: ignore
        for nome, valor in cls.__dict__.items():
            if nome == "__init__" or isinstance(valor, staticmethod):
                setattr(cls, nome, adicionar_prefixo(prefixo)(valor))
            elif isinstance(valor, classmethod):
                setattr(cls, nome, classmethod(adicionar_prefixo(prefixo)(valor.__func__)))
        return cls

    return prefixar_erro_classe

class Result[T]:
    """Classe para capturar o `return | Exception` de chamadas de uma função
    - Alternativa para não propagar o erro e nem precisar utilizar `try-except`

    ```
    # Criando com a função, argumentos posicionais e argumentos nomeados
    # a função será automaticamente chamada após
    result = Result(funcao, "argumento1", "argumento2", argumento=valor)
    # Pode se utilizar como decorador em uma função e obter `Result` como retorno
    @Result.decorador

    # Representação "sucesso" ou "erro"
    repr(result)

    # Checar sucesso na chamada
    if result: ...
    if result.ok()

    # Validação com mensagem de erro
    result.validar("Erro ao realizar xpto")
    valor = result.validar("Erro ao realizar xpto").valor()

    # Acessar
    valor = result.valor()           # necessário checar se é de sucesso
    erro  = result.erro()            # necessário checar se não é de sucesso
    valor = result.valor_ou(default) # valor ou default caso o resultado seja de erro

    # Mapear o resultado para outra função
    Result(lambda: 10 / 1).map(lambda x: x * 2)  # Sucesso; valor=20
    Result(lambda: 1 / 0).map(lambda x: x * 2) # Erro; ZeroDivisionError
    ```"""

    __valor: T | None
    __erro: Exception | None

    def __init__ (self, funcao: typing.Callable[..., T], *args, **kwargs) -> None:
        self.__valor = self.__erro = None
        try: self.__valor = funcao(*args, **kwargs)
        except Exception as erro: self.__erro = erro

    @staticmethod
    def decorador[K] (func: typing.Callable[P, K]) -> typing.Callable[P, Result[K]]: # type: ignore
        """Permite que a classe seja utilizada como um decorador
        - Função"""
        def decorador (*args: P.args, **kwargs: P.kwargs) -> Result[K]: # type: ignore
            return Result(func, *args, **kwargs)
        return decorador

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.__erro is None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Result[T] {"sucesso" if self else "erro"}>"

    def ok (self) -> bool:
        """Indicação de sucesso"""
        return bool(self)

    def valor (self) -> T:
        """Obter o `valor` do resultado
        - `ValueError` necessário validar se o resultado é de sucesso"""
        if not self.ok():
            raise ValueError(f"Tentado obter o valor de um resultado sem sucesso") from self.__erro
        return self.__valor # type: ignore

    def erro (self) -> Exception:
        """Obter o `erro` do resultado
        - `ValueError` Necessário validar se o resultado não é de sucesso"""
        if self.ok():
            raise ValueError(f"Tentado obter o erro de um resultado com sucesso")
        return self.__erro # type: ignore

    def valor_ou[D] (self, default: D) -> T | D:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        return self.__valor if self else default # type: ignore

    def validar (self, mensagem: str) -> typing.Self:
        """Validar se o resultado é de sucesso
        - `Exception(mensagem; erro)` caso não seja um resultado de sucesso
        - Retornado `self` para encadeamento"""
        if not self.ok():
            raise Exception(f"{mensagem}; {self.__erro}")
        return self

    def map[K] (self, func: typing.Callable[[T], K]) -> Result[K]:
        """Aplicar o `valor` do resultado na `func` como primeiro argumento e retornar um novo resultado
        - Caso seja resultado de erro, retornado o mesmo resultado para propagar o erro"""
        if not self.ok(): return self # type: ignore
        return Result(lambda: func(self.__valor)) # type: ignore

__all__ = [
    "retry",
    "Result",
    "adicionar_prefixo",
    "adicionar_prefixo_classe",
]