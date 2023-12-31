# std
from __future__ import annotations
from typing import Generator
from xml.etree.ElementTree import (
    Element,
    parse as xml_from_file,
    tostring as xml_to_string,
    fromstring as xml_from_string
)
# interno
from bot import tipagem


def nome_namespace (tag: str) -> tuple[str, tipagem.url | None]:
    """Extrair nome e namespace da tag"""
    if tag.startswith("{") and "}" in tag:
        idx = tag.index("}")
        return (tag[idx + 1 :], tag[1 : idx])
    else: return (tag, None)


class ElementoXML:
    """Classe de manipulação do XML"""

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

    def __getitem__ (self, index: int) -> ElementoXML:
        """Obter o elemento filho na posição `index` de acordo com o `self.elementos`"""
        return self.elementos[index]

    @property
    def __dict__ (self) -> dict[str, str | None | list[dict]]:
        """Versão `dict` do `ElementoXML`"""
        mapa = { f"@{ nome }": valor for nome, valor in self.atributos.items() } # atributos
        mapa["xmlns"] = self.namespace # namespace
        mapa[self.nome] = [e.__dict__ for e in self] if len(self) else self.texto # elemento: filhos | texto
        return mapa

    @property
    def nome (self) -> str:
        """Nome do elemento"""
        return nome_namespace(self.__e.tag)[0]

    @nome.setter
    def nome (self, nome: str) -> None:
        """Setar nome do elemento"""
        self.__e.tag = nome
    
    @property
    def namespace (self) -> tipagem.url | None:
        """Namespace do elemento"""
        return nome_namespace(self.__e.tag)[1]

    @namespace.setter
    def namespace (self, namespace: tipagem.url | None) -> None:
        """Setar namespace do elemento"""
        nome = nome_namespace(self.__e.tag)[0]
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

    @staticmethod
    def criar (nome: str, texto: str = None, namespace: tipagem.url = None, atributos: dict[str, str] = {}) -> ElementoXML:
        """Criar um `ElementoXML` simples
        - `@staticmethod`"""
        nome = f"{{{ namespace }}}{ nome }" if namespace else nome
        elemento = Element(nome, atributos)
        elemento.text = texto
        return ElementoXML(elemento)


__all__ = [
    "ElementoXML"
]
