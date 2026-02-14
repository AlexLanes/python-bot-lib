# std
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

__all__ = [
    "retry",
    "adicionar_prefixo",
    "adicionar_prefixo_classe",
]