# std
from __future__ import annotations
from typing import Generator, Any
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


__all__ = [
    "yaml_parse",
    "json_parse",
    "ElementoXML",
    "json_stringify",
    "yaml_stringify"
]
