# std
from __future__ import annotations
import ctypes
from inspect import stack
from warnings import simplefilter
from dataclasses import dataclass
from datetime import datetime as Datetime
from itertools import tee as duplicar_iterable
from os.path import getmtime as ultima_alteracao
from typing import Generator, Any, Callable, Self
from json import (
    dumps as json_dumps, 
    loads as json_parse
)
from xml.etree.ElementTree import (
    Element,
    indent as indentar_xml,
    parse as xml_from_file,
    tostring as xml_to_string,
    fromstring as xml_from_string
)
# interno
import bot
# externo
import yaml
from polars import DataFrame
from pywinauto.timings import TimeConfig
from pywinauto import Application, Desktop
from pywinauto.controls.hwndwrapper import HwndWrapper


simplefilter('ignore', category=UserWarning) # ignorar warnings do pywinauto
# reduzir o timeouts busca e fechamento de elemento e janelas
TimeConfig.closeclick_retry = 0.01
TimeConfig.window_find_retry = 0.01
TimeConfig.after_setfocus_wait = 0.01
TimeConfig.after_clickinput_wait = 0.01
TimeConfig.after_setcursorpos_wait = 0.01


def json_stringify (item: Any, indentar=True) -> str:
    """Transforma o `item` em uma string JSON"""
    def tratamentos (obj):
        if type(obj) in (int, float, str, bool, type(None)): return obj
        if hasattr(obj, "__dict__"): return obj.__dict__
        if hasattr(obj, "__iter__"): return [tratamentos(item) for item in obj]
        if hasattr(obj, "__str__"): return obj.__str__()
        raise TypeError(f"Item de tipo inesperado para ser transformado em json: '{type(item)}'")
    return json_dumps(item, ensure_ascii=False, default=tratamentos, indent=4 if indentar else None)


def yaml_stringify (item: Any) -> str:
    """Transforma o `item` em uma string YAML"""
    return yaml.dump(json_parse(json_stringify(item)), sort_keys=False, indent=4)


def yaml_parse (string: str) -> Any:
    """Realizar o parse de uma string YAML"""
    return yaml.load(string, yaml.FullLoader)


class ElementoXML:
    """Classe de manipulação do XML
    - Abstração do módulo `xml.etree.ElementTree`"""

    __e: Element

    def __init__ (self, xml: str) -> None:
        """Inicializar Elemento
        - `xml` pode ser uma string xml ou o caminho até o arquivo .xml"""
        if isinstance(xml, str): # criação exposta do __init__
            xml = xml.lstrip() # remover espaços vazios no começo
            self.__e = xml_from_string(xml) if xml.startswith("<") else xml_from_file(xml).getroot() # parse
        elif isinstance(xml, Element): self.__e = xml # comportamento interno na criação e iteração dos elementos
        else: raise TypeError(f"Tipo '{type(xml)}' inesperado para o xml")

    def __str__ (self) -> str:
        """Versão `text/xml` do ElementoXML"""
        return xml_to_string(self.__e, "unicode")

    def __len__ (self) -> int:
        """Quantidade de elemento(s) filho(s)"""
        return len(self.elementos)

    def __repr__ (self) -> str:
        """Representação do ElementoXML"""
        return f"<ElementoXML '{self.nome}' com {len(self)} elemento(s) filho(s)>"

    def __iter__ (self) -> Generator[ElementoXML, None, None]:
        """Iterator dos elementos"""
        for e in self.elementos: yield e

    def __getitem__ (self, valor: int | str) -> ElementoXML:
        """Obter o elemento filho na posição `int` ou o primeiro elemento de nome `str`"""
        if isinstance(valor, int): 
            if valor >= len(self): raise IndexError(f"Elemento possui apenas '{len(self)}' filho(s)")
            return self.elementos[valor]
        if isinstance(valor, str):
            if not any(e.nome == valor for e in self): raise KeyError(f"Nome do elemento '{valor}' inexistente nos filhos")
            return [e for e in self if e.nome == valor][0]
        raise TypeError(f"Tipo do valor inesperado '{type(valor)}'")

    @property
    def __dict__ (self) -> dict[str, str | None | list[dict]]:
        """Versão `dict` do `ElementoXML`"""
        dicionario = { f"@{nome}": valor for nome, valor in self.atributos.items() } # atributos
        if self.namespace: dicionario["@xmlns"] = self.namespace # namespace
        dicionario[self.nome] = [e.__dict__ for e in self] if len(self) else self.texto # elemento: filhos | texto
        return dicionario

    def __nome_namespace (self) -> tuple[str, bot.tipagem.url | None]:
        """Extrair nome e namespace do `Element` tag
        - `nome, namespace = self.__nome_namespace()`"""
        tag = self.__e.tag
        if tag.startswith("{") and "}" in tag:
            idx = tag.index("}")
            return (tag[idx + 1 :], tag[1 : idx])
        else: return (tag, None)

    @property
    def nome (self) -> str:
        """Nome do elemento"""
        return self.__nome_namespace()[0]

    @nome.setter
    def nome (self, nome: str) -> None:
        """Setar nome do elemento"""
        _, namespace = self.__nome_namespace()
        self.__e.tag = f"{{{namespace}}}{nome}" if namespace else nome

    @property
    def namespace (self) -> bot.tipagem.url | None:
        """Namespace do elemento"""
        return self.__nome_namespace()[1]

    @namespace.setter
    def namespace (self, namespace: bot.tipagem.url | None) -> None:
        """Setar namespace do elemento"""
        nome = self.__nome_namespace()[0]
        self.__e.tag = f"{{{namespace}}}{nome}" if namespace else nome

    @property
    def texto (self) -> str | None:
        """Texto do elemento"""
        return self.__e.text

    @texto.setter
    def texto (self, valor: str | None) -> None:
        """Setar texto"""
        self.__e.text = valor

    @property
    def atributos (self) -> dict[str, str]:
        """Atributos do elemento"""
        return self.__e.attrib
    
    @property
    def elementos (self) -> list[ElementoXML]:
        """Elementos filhos do elemento
        - Para remover ou adicionar elementos, utilizar as funções próprias"""
        return [ElementoXML(e) for e in self.__e]

    def encontrar (self, xpath: str, namespaces: dict[str, bot.tipagem.url] = None) -> list[ElementoXML]:
        """Encontrar elementos que resultem no `xpath` informado
        - `xpath` deve retornar em elementos apenas, não em texto ou atributo
        - `namespaces` para utilizar namespace no `xpath`, informar um dicionario { ns: url }"""
        return [ElementoXML(e) for e in self.__e.findall(xpath, namespaces)]

    def adicionar (self, *elementos: ElementoXML) -> Self:
        """Adicionar os `elementos` na última posição"""
        self.__e.extend(elemento.__e for elemento in elementos)
        return self

    def inserir (self, elemento: ElementoXML, index=0) -> Self:
        """Inserir o `elemento` na posição `index`"""
        self.__e.insert(index, elemento.__e)
        return self

    def remover (self, elemento: ElementoXML) -> Self:
        """Remover `elemento` filho do elemento atual"""
        self.__e.remove(elemento.__e)
        return self

    def indentar (self) -> Self:
        """Indentar o XML
        - Altera a versão do `str()"""
        indentar_xml(self.__e, space=" " * 4)
        return self

    def copiar (self) -> ElementoXML:
        """Criar uma cópia do `ElementoXML`"""
        return ElementoXML(str(self))

    @classmethod
    def criar (cls, nome: str, texto: str = None, namespace: bot.tipagem.url = None, atributos: dict[str, str] = {}) -> ElementoXML:
        """Criar um `ElementoXML` simples
        - `@classmethod`"""
        nome = f"{{{namespace}}}{nome}" if namespace else nome
        elemento = Element(nome, atributos)
        elemento.text = texto
        return cls(elemento)


@dataclass
class Coordenada:
    """Coordenada de uma região na tela"""
    x: int
    y: int
    largura: int
    altura: int

    def __iter__ (self):
        """Utilizado com o `tuple(coordenada)` e `x, y, largura, altura = coordenada`"""
        yield self.x
        yield self.y
        yield self.largura
        yield self.altura

    def __len__ (self):
        return 4

    def __contains__ (self, other: Coordenada | tuple[int, int]) -> bool:
        """Testar se o ponto central da coordenada está dentro da outra
        - `coordenada in coordenada2`"""
        if not isinstance(other, Coordenada) and not isinstance(other, tuple):
            return False

        x, y = other.transformar() if isinstance(other, Coordenada) else other
        return x in range(self.x, self.x + self.largura + 1) \
           and y in range(self.y, self.y + self.altura + 1)

    def transformar (self, xOffset=0.5, yOffset=0.5) -> tuple[int, int]:
        """Transformar as cordenadas para a posição (X, Y) de acordo com a porcentagem `xOffset` e `yOffset`
        - (X, Y) central caso os offsets não tenham sido informados
        - `xOffset` esquerda, centro, direita = 0.0, 0.5, 1.0
        - `yOffset` topo, centro, baixo = 0.0, 0.5, 1.0"""
        # enforça o range entre 0.0 e 1.0
        xOffset, yOffset = max(0.0, min(1.0, xOffset)), max(0.0, min(1.0, yOffset))
        return (self.x + int(self.largura * xOffset), 
                self.y + int(self.altura * yOffset))

    @classmethod
    def from_box (cls, box: tuple[int, int, int, int]) -> Coordenada:
        """Criar coordenada a partir de uma box
        - `box`: `X esquerda-direita` + `Y esquerda-direita`
        - `@classmethod`"""
        x, y = int(box[0]), int(box[2])
        largura, altura = int(box[1] - x), int(box[3] - y)
        return cls(x, y, largura, altura)


@dataclass
class ResultadoSQL:
    """Classe utilizada no retorno da execução do banco de dados"""
    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica para o comando sql"""
    colunas: tuple[str, ...]
    """Colunas das linhas retornadas (se houver)"""
    linhas: Generator[tuple[bot.tipagem.tipoSQL, ...], None, None]
    """Generator das linhas retornadas (se houver)
    - Consumido quando iterado sobre"""

    def __iter__ (self) -> Generator[tuple[bot.tipagem.tipoSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas:
            yield linha

    def __repr__ (self) -> str:
        "Representação da classe"
        possui_linhas = False
        self.linhas, linhas = duplicar_iterable(self.linhas)
        try: possui_linhas = bool(next(linhas))
        except: pass

        tipo = f"com {self.linhas_afetadas} linha(s) afetada(s)" if self.linhas_afetadas \
          else f"com {len(self.colunas)} coluna(s) e {len(self)} linha(s)" if possui_linhas \
          else f"vazio"

        return f"<ResultadoSQL {tipo}>"

    def __bool__ (self) -> bool:
        """Representação se possui linhas ou linhas_afetadas"""
        return "vazio" not in repr(self)

    def __len__ (self) -> int:
        """Obter a quantidade de linhas no retornadas"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        return sum(1 for _ in linhas)

    def __getitem__ (self, campo: str) -> bot.tipagem.tipoSQL:
        """Obter um campo da primeira linha"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        linha = next(linhas)
        return linha[self.colunas.index(campo)]

    @property
    def __dict__ (self) -> dict[str, int | None | list[dict]]:
        """Representação formato dicionário"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        return {
            "linhas_afetadas": self.linhas_afetadas,
            "resultados": [{ coluna: valor for coluna, valor in zip(self.colunas, linha) } 
                           for linha in linhas]
        }

    def to_dataframe (self, transformar_string=False) -> DataFrame:
        """Salvar o resultado em um `polars.DataFrame`
        - `transformar_string` flag se os dados serão convertidos em `str`"""
        self.linhas, linhas = duplicar_iterable(self.linhas)
        return DataFrame(
            (
                tuple(str(valor) if valor != None else valor
                      for valor in linha)
                for linha in linhas
            ) if transformar_string else linhas, 
            self.colunas,
            nan_to_null=True
        )


class Resultado [T]:
    """Classe `genérica` de utilização para retornar resultado ou erro de alguma chamada"""
    __valor: T | None
    __erro: Exception | None

    def __init__ (self, funcao: Callable[[], T], *args, **kwargs) -> None:
        """Realizar a chamada na `função` com os argumentos `args` e `kwargs`"""
        try:
            self.__valor = funcao(*args, **kwargs)
            self.__erro = None
        except Exception as erro:
            bot.logger.alertar(f"Função '{funcao.__name__}' executada pelo <Resultado[T]> apresentou erro")
            self.__valor = None
            self.__erro = erro

    def __bool__ (self) -> bool:
        """Indicação de sucesso"""
        return self.__erro == None

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Resultado[T] {"com" if self else "sem"} valor>"

    def valor (self) -> T:
        """Obter o valor do resultado
        - `raise Exception` caso tenha apresentado erro"""
        if not self:
            self.__erro.add_note("Valor não presente no resultado")
            raise self.__erro
        return self.__valor

    def valor_ou (self, default: T) -> T:
        """Obter o valor do resultado ou `default` caso tenha apresentado erro"""
        if not self: return default
        return self.__valor


@dataclass
class Diretorio:
    """Armazena os caminhos de pastas e arquivos presentes no diretório"""
    caminho: bot.tipagem.caminho
    """Caminho absoluto do diretorio"""
    pastas: list[bot.tipagem.caminho]
    """Lista contendo o caminho de cada pasta do diretório"""
    arquivos: list[bot.tipagem.caminho]
    """Lista contendo o caminho de cada arquivo do diretório"""

    def query_data_alteracao_arquivos (self,
                                       inicio=Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                       fim=Datetime.now()) -> list[tuple[bot.tipagem.caminho, Datetime]]:
        """Consultar arquivos do diretório com base na data de alteração
        - Default: Hoje
        - Retorna uma lista `(caminho, data)` ordenado pelos mais antigos"""
        ordenar_antigos = lambda x: x[1]
        criar_data = lambda caminho: Datetime.fromtimestamp(ultima_alteracao(caminho))

        arquivos = [(caminho, data) for caminho in self.arquivos
                    if inicio <= (data := criar_data(caminho)) <= fim]
        arquivos.sort(key=ordenar_antigos)

        return arquivos


class InfoStack:
    """Informações do `Stack` de execução"""
    nome: str
    """Nome do arquivo"""
    funcao: str
    """Nome da função"""
    linha: int
    """Linha do item executado"""
    caminho: bot.tipagem.caminho
    """Caminho do arquivo"""

    def __init__ (self, index=1) -> None:
        """Obter informações presente no stack dos callers
        - `Default` arquivo que chamou o `InfoStack()`"""
        self.linha = stack()[index].lineno
        self.funcao = stack()[index].function
        caminho, self.nome = stack()[index].filename.rsplit("\\", 1)
        self.caminho = f"{caminho[0].upper()}{caminho[1:]}" # forçar upper no primeiro char


@dataclass
class Email:
    """Classe para armazenar informações extraídas de Email"""
    uid: int
    """id do e-mail"""
    remetente: bot.tipagem.email
    """Remetente que enviou o e-mail"""
    destinatarios: list[bot.tipagem.email]
    """Destinatários que receberam o e-mail"""
    assunto: str
    """Assunto do e-mail"""
    data: Datetime
    """Data de envio do e-mail"""
    texto: str | None
    """Conteúdo do e-mail como texto"""
    html: str | None
    """Conteúdo do e-mail como html"""
    anexos: list[tuple[str, str, bytes]]
    """Anexos do e-mail
    - `for nome, tipo, conteudo in email.anexos:`"""


class Janela:
    """Classe de interação com as janelas abertas. 
    - Abstração do `pywinauto`"""

    __janela: HwndWrapper
    """Conexão com a janela superior"""
    __aplicacao: Application
    """Application da janela"""

    def __init__ (self, titulo: str = None, class_name: str = None, backend: bot.tipagem.BACKENDS_JANELA = "win32") -> None:
        """Inicializar a conexão com a janela
        - Se o `titulo` e `class_name` forem omitidos, será pego a janela focada atual
        - `backend` varia de acordo com a janela, testar com ambos para encontrar o melhor"""
        if not titulo and not class_name:
            handle = ctypes.windll.user32.GetForegroundWindow()
            self.__janela = Desktop(backend).window(handle=handle)
            self.__aplicacao = Application(backend).connect(handle=handle)
            return

        titulo_normalizado = bot.util.normalizar(titulo)
        titulos = [titulo for titulo in self.titulos_janelas()
                   if titulo_normalizado in bot.util.normalizar(titulo)]
        assert titulos, f"Janela de titulo '{titulo}' não foi encontrada"

        self.__janela = Desktop(backend).window(title=titulos[0], class_name=class_name, visible_only=True)
        self.__aplicacao = Application(backend).connect(title=titulos[0], class_name=class_name, visible_only=True)

    def __eq__ (self, other) -> bool:
        """Comparar se o handler de uma janela é o mesmo que a outra"""
        if not isinstance(other, Janela): return False
        return self.__janela.handle == other.__janela.handle

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Janela '{self.titulo}'>"

    @property
    def titulo (self) -> str:
        """Titulo da janela"""
        return self.__janela.window_text()
    @property
    def maximizada (self) -> bool:
        """Checar se a janela está maximizada"""
        return self.__janela.is_maximized()
    @property
    def minimizada (self) -> bool:
        """Checar se a janela está minimizada"""
        return self.__janela.is_minimized()
    @property
    def focada (self) -> bool:
        """Checar se a janela está focada"""
        return self.__janela.is_active()
    @property
    def coordenada (self) -> Coordenada:
        """Coordenada da janela
        - `Coordenada` zerada caso a janela esteja minimizada"""
        box = self.__janela.rectangle()
        return Coordenada(box.left, box.top, box.width(), box.height())

    def minimizar (self) -> Self:
        """Minimizar janela"""
        self.__janela.minimize()
        return self
    def maximizar (self) -> Self:
        """Maximizar janela"""
        self.__janela.maximize()
        return self
    def restaurar (self) -> Self:
        """Restaurar a janela para o estado anterior"""
        self.__janela.restore()
        return self
    def focar (self) -> Self:
        """Focar na janela"""
        if self.minimizada: self.restaurar()
        self.__janela.set_focus()
        return self
    def fechar (self) -> None:
        """Fechar janela"""
        self.__aplicacao.kill()

    def elementos (self, *, title: str = None, title_re: str = None,
                   class_name: str = None, control_id: int = None,
                   top_level_only=True, visible_only=True, enabled_only=True) -> list[HwndWrapper]:
        """Obter uma lista elementos com base nos parâmetros informados
        - O tipo do retorno pode ser diferente dependendo do tipo do backend e controle
        - Retornado uma classe genérica que compartilham múltiplos métodos"""
        return self.__aplicacao.windows(title=title, title_re=title_re, class_name=class_name,
                                        control_id=control_id, top_level_only=top_level_only,
                                        visible_only=visible_only, enabled_only=enabled_only)

    @staticmethod
    def titulos_janelas () -> set[str]:
        """Listar os titulos das janelas abertas
        - `@staticmethod`"""
        janelas: list[HwndWrapper] = Desktop().windows(visible_only=True)
        return { titulo
                 for janela in janelas 
                 if (titulo := janela.window_text()) }


__all__ = [
    "Email",
    "Janela",
    "InfoStack",
    "Diretorio",
    "Resultado",
    "yaml_parse",
    "json_parse",
    "Coordenada",
    "ElementoXML",
    "ResultadoSQL",
    "json_stringify",
    "yaml_stringify"
]
