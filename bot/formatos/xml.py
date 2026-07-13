# std
from __future__ import annotations
import base64
from typing import Generator, Self
from xml.etree.ElementTree import (
    Element,
    register_namespace,
    parse       as xml_from_file,
    indent      as indentar_xml,
    tostring    as xml_to_string,
    fromstring  as xml_from_string,
)
# interno
import bot

class ElementoXML:
    """Classe de manipulação e criação de XML
    - Abstração do módulo `xml.etree.ElementTree`

    ```
    # Parse
    ElementoXML.Parse(bot.sistema.Caminho("arquivo.xml"))
    ElementoXML.Parse('<raiz versão="1"><filho1>abc</filho1><filho2>xyz</filho2></raiz>')
    ElementoXML.ParseB64("PHJhaXogdmVyc8Ojbz0iMSI+PGZpbGhvMT5hYmM8L2ZpbGhvMT48ZmlsaG8yPnh5ejwvZmlsaG8yPjwvcmFpej4=")

    # Criação de elementos
    raiz = ElementoXML("raiz", atributos={ "versão": "1" })
    raiz.adicionar(ElementoXML("filho1", "abc"), ElementoXML("filho2", "xyz"))
    print(raiz) # <raiz versão="1"><filho1>abc</filho1><filho2>xyz</filho2></raiz>

    # Atributos
    raiz.nome       # Nome do elemento
    raiz.texto      # Texto do elemento (se houver)
    raiz.atributos  # Atributos do elemento
    raiz.namespace  # Namespace do elemento (se houver)

    # Acessores
    len(raiz)               # Quantidade de elemento(s) filho(s)
    str(raiz)               # Versão `text/xml` do ElementoXML
    bool(raiz)              # Formato `bool` indicando se possui algum filho ou texto
    for filho in raiz: ...  # Iterator dos `elementos` filhos

    # Métodos
    raiz.adicionar()    # Adicionar `n` elementos como filho
    raiz.inserir()      # Inserir elemento no index informado
    raiz.elementos()    # Elementos filhos
    raiz.remover()      # Remover elemento descendente do elemento
    raiz.indentar()     # Indentar a verão `str()` do xml
    raiz.copiar()       # Criar uma cópia do elemento
    raiz.to_dict()      # Versão `dict` do elemento

    # Registrar um namespace para utilizar na procura com o xpath
    ElementoXML.registrar_prefixo("ns", "url")
    # Procurar elementos que resultem no xpath informado
    raiz.procurar(xpath="", namespaces={})
    # Encontrar elemento que resulte no xpath informado ou `None` caso não seja encontrado
    raiz.encontrar(xpath="", namespaces={})
    ```"""

    __elemento: Element
    __prefixos: dict[str, bot.tipagem.url] = {}

    def __init__ (self, nome: str,
                        texto: str | None = None,
                        namespace: bot.tipagem.url | None = None,
                        atributos: dict[str, str] | None = None) -> None:
        nome = f"{{{namespace}}}{nome}" if namespace else nome
        self.__elemento = Element(nome, atributos or {})
        self.__elemento.text = texto

    @classmethod
    def Parse (cls, xml: str | bot.sistema.Caminho) -> ElementoXML:
        """Parse do `xml` para um `ElementoXML`
        - `xml` pode ser uma string xml ou o caminho até o arquivo .xml"""
        xml = str(xml).lstrip() # remover espaços vazios no começo
        element = xml_from_string(xml) if xml.startswith("<") else xml_from_file(xml).getroot()
        return ElementoXML.__from_element(element)

    @classmethod
    def ParseB64 (cls, xml: str) -> ElementoXML:
        """Parse do `xml`, formato base64, para um `ElementoXML`
        - `Exception` caso ocorra erro"""
        try: xml = base64.b64decode(xml).decode()
        except Exception:
            raise Exception("Falha ao realizar o parse de XML no formato base64")
        return ElementoXML.Parse(xml)

    @classmethod
    def __from_element (cls, element: Element) -> ElementoXML:
        """Criação do `ElementoXML` diretamente com um `Element`"""
        elemento = cls.__new__(cls)
        elemento.__elemento = element
        return elemento

    def __str__ (self) -> str:
        """Versão `text/xml` do ElementoXML"""
        return xml_to_string(self.__elemento, "unicode")

    def __len__ (self) -> int:
        """Quantidade de elemento(s) filho(s)"""
        return len(self.elementos())

    def __repr__ (self) -> str:
        """Representação do ElementoXML"""
        return f"<ElementoXML '{self.nome}' com {len(self)} elemento(s) filho(s)>"

    def __iter__ (self) -> Generator[ElementoXML, None, None]:
        """Iterator dos `elementos` filhos"""
        for elemento in self.elementos():
            yield elemento

    def __bool__ (self) -> bool:
        """Formato `bool` indicando se possui algum filho ou texto"""
        return bool(len(self) or self.texto)

    def __getitem__ (self, value: int | str) -> ElementoXML | None:
        """Obter o elemento filho na posição `int` ou o primeiro elemento de nome `str`
        - `None` caso não seja possível"""
        elementos = self.elementos()
        if isinstance(value, int) and value < len(elementos):
            return elementos[value]
        for elemento in elementos:
            if elemento.nome == str(value):
                return elemento
        return None

    @property
    def nome (self) -> str:
        """`Nome` do elemento"""
        return self.__nome_namespace()[0]

    @nome.setter
    def nome (self, nome: str) -> None:
        """Setar `nome` do elemento"""
        _, namespace = self.__nome_namespace()
        self.__elemento.tag = f"{{{namespace}}}{nome}" if namespace else nome

    @property
    def namespace (self) -> bot.tipagem.url | None:
        """`Namespace` do elemento
        - Não leva em conta o `xmlns` do parente"""
        return self.__nome_namespace()[1]

    @namespace.setter
    def namespace (self, namespace: bot.tipagem.url | None) -> None:
        """Setar `namespace` do elemento"""
        nome, _ = self.__nome_namespace()
        self.__elemento.tag = f"{{{namespace}}}{nome}" if namespace else nome

    @property
    def texto (self) -> str | None:
        """`Texto` do elemento"""
        return self.__elemento.text

    @texto.setter
    def texto (self, valor: str | None) -> None:
        """Setar `texto`"""
        self.__elemento.text = valor

    @property
    def atributos (self) -> dict[str, str]:
        """`Atributos` do elemento"""
        return self.__elemento.attrib

    @atributos.setter
    def atributos (self, valor: dict[str, str]) -> None:
        """Setar `atributos`"""
        self.__elemento.attrib = valor

    def __nome_namespace (self) -> tuple[str, bot.tipagem.url | None]:
        """Extrair nome e namespace do `Element.tag`
        - `nome, namespace = self.__nome_namespace()`"""
        tag = self.__elemento.tag
        if tag.startswith("{") and "}" in tag:
            idx = tag.index("}")
            return (tag[idx + 1 :], tag[1 : idx])
        else: return (tag, None)

    def to_dict (self) -> dict[str, str | None | list[dict]]:
        """Versão `dict` do `ElementoXML`"""
        elemento = {}
        # atributos
        elemento.update({
            f"@{nome}": valor
            for nome, valor in self.atributos.items()
        })
        # namespace
        if ns := self.namespace:
            prefixo = ([p for p, url in self.__prefixos.items() if url == ns] or ["ns"])[0]
            elemento.update({ f"@xmlns:{prefixo}": ns })
        # elemento = filhos ou texto
        elemento[self.nome] = [e.to_dict() for e in self] if len(self) else self.texto
        return elemento

    def elementos (self) -> list[ElementoXML]:
        """Elementos filhos do elemento
        - Para remover ou adicionar elementos, utilizar as funções próprias"""
        return [
            ElementoXML.__from_element(elemento)
            for elemento in self.__elemento
        ]

    def encontrar (self, xpath: str, namespaces: dict[str, bot.tipagem.url] | None = None) -> ElementoXML | None:
        """Encontrar elemento que resulte no `xpath` informado ou `None` caso não seja encontrado
        - `xpath` deve retornar no elemento apenas, não em texto ou atributo
        - `namespaces` para utilizar prefixos no `xpath`, informar um dicionario `{ ns: url } ou registrar_prefixo()`"""
        p = self.__prefixos
        namespaces = { **namespaces, **p } if namespaces else p
        xpath = xpath if xpath.startswith(".") else f".{xpath}"
        elemento = self.__elemento.find(xpath, namespaces)
        return ElementoXML.__from_element(elemento) if elemento != None else None

    def procurar (self, xpath: str, namespaces: dict[str, bot.tipagem.url] | None = None) -> list[ElementoXML]:
        """Procurar elementos que resultem no `xpath` informado
        - `xpath` deve retornar em elementos apenas, não em texto ou atributo
        - `namespaces` para utilizar prefixos no `xpath`, informar um dicionario `{ ns: url } ou registrar_prefixo()`"""
        p = self.__prefixos
        namespaces = { **namespaces, **p } if namespaces else p
        xpath = xpath if xpath.startswith(".") else f".{xpath}"
        return [
            ElementoXML.__from_element(element)
            for element in self.__elemento.findall(xpath, namespaces)
        ]

    def adicionar (self, *elementos: ElementoXML) -> Self:
        """Adicionar os `elementos` na última posição"""
        self.__elemento.extend(
            elemento.__elemento
            for elemento in elementos
        )
        return self

    def inserir (self, elemento: ElementoXML, index=0) -> Self:
        """Inserir o `elemento` na posição `index`"""
        self.__elemento.insert(index, elemento.__elemento)
        return self

    def remover (self, elemento: ElementoXML) -> Self:
        """Remover `elemento` descendente do elemento atual"""
        try: self.__elemento.remove(elemento.__elemento)
        except ValueError: any(e.remover(elemento) for e in self)
        return self

    def indentar (self) -> Self:
        """Indentar o XML
        - Altera a versão do `str()"""
        indentar_xml(self.__elemento, space=" " * 4)
        return self

    def copiar (self) -> ElementoXML:
        """Criar uma cópia do `ElementoXML`"""
        return ElementoXML.Parse(str(self))

    @staticmethod
    def registrar_prefixo (prefixo: str, namespace: bot.tipagem.url) -> bot.tipagem.url:
        """Registrar o `prefixo` para o determinado `namespace`
        - Retorna o `namespace`"""
        ElementoXML.__prefixos[prefixo] = namespace
        return register_namespace(prefixo, namespace) or namespace

__all__ = ["ElementoXML"]