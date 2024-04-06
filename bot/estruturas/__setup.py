# std
from __future__ import annotations
from itertools import chain, tee
from dataclasses import dataclass
from typing import Generator, Any
from datetime import datetime as Datetime
from os.path import getmtime as ultima_alteracao
from json import (
    dumps as json_dumps, 
    loads as json_parse
)
from xml.etree.ElementTree import (
    Element,
    parse as xml_from_file,
    tostring as xml_to_string,
    fromstring as xml_from_string
)
# interno
from bot import tipagem
# externo
import yaml
from polars import DataFrame


def json_stringify (item: Any, indentar=True) -> str:
    """Transforma o `item` em uma string JSON"""
    def tratamentos (obj):
        if type(obj) in (int, float, str, bool, type(None)): return obj
        if hasattr(obj, "__dict__"): return obj.__dict__
        if hasattr(obj, "__iter__"): return [tratamentos(item) for item in obj]
        if hasattr(obj, "__str__"): return obj.__str__()
        raise TypeError(f"Item de tipo inesperado para ser transformado em json: '{ type(item) }'")
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
        else: raise TypeError(f"Tipo '{ type(xml) }' inesperado para o xml")

    def __str__ (self) -> str:
        """Versão `text/xml` do ElementoXML"""
        return xml_to_string(self.__e, "unicode")

    def __len__ (self) -> int:
        """Quantidade de elemento(s) filho(s)"""
        return len(self.elementos)

    def __repr__ (self) -> str:
        """Representação do ElementoXML"""
        return f"<ElementoXML '{ self.nome }' com { len(self) } elemento(s) filho(s)>"

    def __iter__ (self) -> Generator[ElementoXML, None, None]:
        """Iterator dos elementos"""
        for e in self.elementos: yield e

    def __getitem__ (self, valor: int | str) -> ElementoXML:
        """Obter o elemento filho na posição `int` ou o primeiro elemento de nome `str`"""
        if isinstance(valor, int): 
            if valor >= len(self): raise IndexError(f"Elemento possui apenas '{ len(self) }' filho(s)")
            return self.elementos[valor]
        if isinstance(valor, str):
            if not any(e.nome == valor for e in self): raise KeyError(f"Nome do elemento '{ valor }' inexistente nos filhos")
            return [e for e in self if e.nome == valor][0]
        raise TypeError(f"Tipo do valor inesperado '{ type(valor) }'")

    @property
    def __dict__ (self) -> dict[str, str | None | list[dict]]:
        """Versão `dict` do `ElementoXML`"""
        dicionario = { f"@{ nome }": valor for nome, valor in self.atributos.items() } # atributos
        if self.namespace: dicionario["@xmlns"] = self.namespace # namespace
        dicionario[self.nome] = [e.__dict__ for e in self] if len(self) else self.texto # elemento: filhos | texto
        return dicionario

    def __nome_namespace (self) -> tuple[str, tipagem.url | None]:
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
        self.__e.tag = f"{{{ namespace }}}{ nome }" if namespace else nome

    @property
    def namespace (self) -> tipagem.url | None:
        """Namespace do elemento"""
        return self.__nome_namespace()[1]

    @namespace.setter
    def namespace (self, namespace: tipagem.url | None) -> None:
        """Setar namespace do elemento"""
        nome = self.__nome_namespace()[0]
        self.__e.tag = f"{{{ namespace }}}{ nome }" if namespace else nome

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

    def encontrar (self, xpath: str, namespaces: dict[str, str] = None) -> list[ElementoXML]:
        """Encontrar elementos que resultem no `xpath` informado
        - `xpath` deve retornar em elementos apenas, não em texto ou atributo
        - `namespaces` para utilizar namespace no `xpath`, informar um dicionario { ns: url }"""
        return [ElementoXML(e) for e in self.__e.findall(xpath, namespaces)]

    def adicionar (self, elemento: ElementoXML) -> None:
        """Adicionar `elemento` como último filho"""
        self.__e.append(elemento.__e)

    def remover (self, elemento: ElementoXML) -> None:
        """Remover `elemento` filho do elemento atual"""
        self.__e.remove(elemento.__e)

    def copiar (self) -> ElementoXML:
        """Criar uma cópia do `ElementoXML`"""
        return ElementoXML(str(self))

    @classmethod
    def criar (cls, nome: str, texto: str = None, namespace: tipagem.url = None, atributos: dict[str, str] = {}) -> ElementoXML:
        """Criar um `ElementoXML` simples
        - `@classmethod`"""
        nome = f"{{{ namespace }}}{ nome }" if namespace else nome
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

    def __contains__ (self, c) -> bool:
        """Testar se o ponto central da coordenada está dentro da outra
        - `coordenada in coordenada2`"""
        if not isinstance(c, Coordenada): return False
        x, y = self.transformar()
        return x in range(c.x, c.x + c.largura + 1) and y in range(c.y, c.y + c.altura + 1)

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
    linhas: Generator[tuple[tipagem.tiposSQL, ...], None, None]
    """Generator das linhas retornadas (se houver)"""

    def __iter__ (self) -> Generator[tuple[tipagem.tiposSQL, ...], None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas: yield linha

    def __repr__ (self) -> str:
        "Representação da classe"
        linhas, possui_linhas = self.linhas, False
        try: 
            self.linhas = chain([next(linhas)], linhas)
            possui_linhas = True
        except StopIteration: pass

        tipo = f"com '{ self.linhas_afetadas }' linha(s) afetada(s)" if self.linhas_afetadas \
          else f"com linha(s) e '{ len(self.colunas) }' coluna(s)" if possui_linhas \
          else f"vazio"
        return f"<ResultadoSQL { tipo }>"

    def __bool__ (self) -> bool:
        """Representação booleana"""
        return "vazio" not in repr(self)

    @property
    def __dict__ (self) -> dict[str, int | None | list[dict]]:
        """Representação formato dicionário"""
        linhas = [*self] # linhas do gerador
        self.linhas = (linha for linha in linhas) # recriar gerador
        return {
            "linhas_afetadas": self.linhas_afetadas,
            "resultados": [{ coluna: valor for coluna, valor in zip(self.colunas, linha) } 
                           for linha in linhas]
        }

    def to_dataframe (self) -> DataFrame:
        """Salvar o resultado em um `polars.DataFrame`"""
        self.linhas, linhas = tee(self.linhas)
        return DataFrame(linhas, self.colunas, nan_to_null=True)


@dataclass
class Diretorio:
    """Armazena os caminhos de pastas e arquivos presentes no diretório"""
    caminho: tipagem.caminho
    """Caminho absoluto do diretorio"""
    pastas: list[tipagem.caminho]
    """Lista contendo o caminho de cada pasta do diretório"""
    arquivos: list[tipagem.caminho]
    """Lista contendo o caminho de cada arquivo do diretório"""

    def query_data_alteracao_arquivos (self,
                                       inicio=Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                                       fim=Datetime.now()) -> list[tuple[tipagem.caminho, Datetime]]:
        """Consultar arquivos do diretório com base na data de alteração
        - Default: Hoje
        - Retorna uma lista `(caminho, data)` ordenado pelos mais antigos"""
        ordenar_antigos = lambda x: x[1]
        criar_data = lambda caminho: Datetime.fromtimestamp(ultima_alteracao(caminho))

        arquivos = [(caminho, data) for caminho in self.arquivos
                    if inicio <= (data := criar_data(caminho)) <= fim]
        arquivos.sort(key=ordenar_antigos)

        return arquivos


@dataclass
class InfoStack:
    """Informações retiradas do Stack de execução"""
    nome: str
    """Nome arquivo"""
    caminho: tipagem.caminho
    """Caminho arquivo"""
    funcao: str
    """Nome da função"""
    linha: int
    """Linha do item executado"""


@dataclass
class Email:
    """Classe para armazenar informações extraídas de Email"""
    uid: int
    """id do e-mail"""
    remetente: tipagem.email
    """Remetente que enviou o e-mail"""
    destinatarios: list[tipagem.email]
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


__all__ = [
    "Email",
    "InfoStack",
    "Diretorio",
    "yaml_parse",
    "json_parse",
    "Coordenada",
    "ElementoXML",
    "ResultadoSQL",
    "json_stringify",
    "yaml_stringify"
]
