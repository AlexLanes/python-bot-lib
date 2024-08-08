# std
from __future__ import annotations
from typing import Generator, Any, Self
from json import (
    JSONDecodeError,
    dumps as json_dumps, 
    loads as json_parse
)
from xml.etree.ElementTree import (
    Element,
    register_namespace,
    indent as indentar_xml,
    parse as xml_from_file,
    tostring as xml_to_string,
    fromstring as xml_from_string,
)
# interno
from .. import logger, tipagem
# externo
import yaml
from jsonschema import (
    SchemaError,
    ValidationError,
    validate as validate_schema
)

def yaml_stringify (item: Any) -> str:
    """Transforma o `item` em uma string YAML"""
    return yaml.dump(Json(item).stringify(), sort_keys=False, indent=4)

def yaml_parse (string: str) -> Any:
    """Realizar o parse de uma string YAML"""
    return yaml.load(string, yaml.FullLoader)

class Json [T]:
    """Classe para validação e leitura de objetos JSON

    ```
    item = { "nome": "Alex", "dados": [{ "marco": "polo" }] }
    json = bot.formatos.Json(item)
    # Caminho valido
    print(json.nome.valor(), "|", f"Valido: {bool(json.nome)}")
    print(json["dados"].valor(), "|", f"Valido: {bool(json["dados"])}")
    print(json.dados[0].valor(), "|", f"Valido: {bool(json.dados[0])}")
    print(json.dados[0].marco.valor(), "|", f"Valido: {bool(json.dados[0].marco)}")
    # Caminho invalido
    print(json.dados[1].valor(), "|", f"Valido: {bool(json.dados[1])}")
    print(json.dados[1]["abc"].valor(), "|", f"Valido: {bool(json.dados[1]["abc"])}")
    # Comparação
    print(bool(json.nome))
    print("Caminho existe" if json.dados[0].marco else "Caminho não existe")
    print(json.nome == "Alex")
    print(json.nome != "Xyz")
    print({ "marco": "polo" } in json.dados)
    # Funções
    print(repr(json))
    print("Obtendo o tipo do json:", json.tipo())
    print("Obtendo o valor do json:", json.valor())
    print("Transformando em string:", json.stringify(indentar=False))
    print("Realizar parse de uma string json:", bot.formatos.Json.parse("[1, 2, 3]").valor())
    print("Validar um Json de acordo com o jsonschema:", json.validar({ "type": "object", "properties": {"nome": {"type": "string"}} }))
    ```"""

    __item: T
    """Representação JSON como objeto Python"""
    __valido: bool
    """Indicador se o caminho percorrido no `json` é valido"""

    def __init__ (self, item: T) -> None:
        self.__item = item
        self.__valido = True

    def __repr__ (self) -> str:
        """Representação da classe"""
        tipo = self.tipo().__name__
        return f"<Json [{tipo}]>"

    def __bool__ (self) -> bool:
        """Indicador se o caminho percorrido no `json` é valido"""
        return self.__valido

    def __getattr__ (self, chave: str) -> Json:
        return self[chave]

    def __getitem__ (self, valor: int | str) -> Json:
        """Obter o item filho na posição `int` ou elemento de nome `str`
        - Invalidar o `json` se o caminho for invalido"""
        try:
            if self.tipo() in (list, tuple, dict):
                return Json(self.__item[valor])

        # caminho inválido
        except (KeyError, IndexError): pass
        json = Json(None)
        json.__valido = False
        return json

    def __eq__ (self, value: object) -> bool:
        """Comparador `==` do valor"""
        return self.valor() == value

    def __ne__ (self, value: object) -> bool:
        """Comparador `!=` do valor"""
        return self.valor() != value

    def __contains__ (self, value: object) -> bool:
        """Comparador `in` do valor"""
        return value in self.valor() if self.tipo() in (list, tuple, dict, str) else False

    def tipo (self) -> type[T]:
        """Tipo atual do `json`"""
        return type(self.__item)

    def valor (self) -> T:
        """Valor atual do `json`"""
        return self.__item

    def stringify (self, indentar=True) -> str:
        """Transformar o `json` no formato string"""
        def tratamentos (obj):
            if type(obj) in (int, float, str, bool, type(None)): return obj
            if hasattr(obj, "__dict__"): return obj.__dict__
            if hasattr(obj, "__iter__"): return [tratamentos(item) for item in obj]
            if hasattr(obj, "__str__"): return obj.__str__()
            raise TypeError(f"Tipo inesperado para ser transformado em json: '{type(obj)}'")
        return json_dumps(self.__item, ensure_ascii=False, default=tratamentos, indent=4 if indentar else None)

    def validar (self, schema: dict) -> bool:
        """Validar se o `json` está de acordo com o `schema`"""
        try: return validate_schema(self.__item, schema) == None
        except SchemaError as erro:
            logger.alertar(f"Schema de validação do {self} apresentou erro\n\t{erro.message}\n\t{schema}")
        except ValidationError as erro:
            logger.alertar(f"Validação do {self} apresentou erro\n\t{erro.message}\n\t{self.__item}")
        return False

    @classmethod
    def parse (cls, json: str) -> Json | None:
        """Realiza o parse de uma string JSON na classe `Json`
        - `None` caso ocorra falha"""
        try: return Json(json_parse(json))
        except JSONDecodeError as erro:
            return logger.alertar(f"Falha ao realizar o parse no json\n\t{json}\n\t{erro.msg}")

class ElementoXML:
    """Classe de manipulação do XML
    - Abstração do módulo `xml.etree.ElementTree`"""

    __elemento: Element
    __prefixos: dict[str, tipagem.url] = {}

    def __init__ (self, nome: str, texto: str = None, namespace: tipagem.url = None, atributos: dict[str, str] = None) -> None:
        nome = f"{{{namespace}}}{nome}" if namespace else nome
        self.__elemento = Element(nome, atributos or {})
        self.__elemento.text = texto

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
        """Iterator dos `elementos`"""
        for elemento in self.elementos():
            yield elemento

    def __bool__ (self) -> bool:
        """Formato `bool`"""
        return bool(len(self) or self.texto)

    def __getitem__ (self, valor: int | str) -> ElementoXML | None:
        """Obter o elemento filho na posição `int` ou o primeiro elemento de nome `str`
        - `None` caso não seja possível"""
        elementos = self.elementos()
        if isinstance(valor, int) and valor < len(elementos):
            return elementos[valor]
        if isinstance(valor, str) and any(e.nome == valor for e in elementos):
            return [e for e in elementos if e.nome == valor][0]
        return None

    @property
    def __dict__ (self) -> dict[str, str | None | list[dict]]:
        """Versão `dict` do `ElementoXML`"""
        elemento = {}
        # atributos
        elemento.update({ f"@{nome}": valor for nome, valor in self.atributos.items() })
        # namespace
        if ns := self.namespace:
            prefixo = ([p for p, url in self.__prefixos.items() if url == ns] or ["ns"])[0]
            elemento.update({ f"@xmlns:{prefixo}": ns })
        # elemento = filhos ou texto
        elemento[self.nome] = [e.__dict__ for e in self] if len(self) else self.texto
        return elemento

    def __nome_namespace (self) -> tuple[str, tipagem.url | None]:
        """Extrair nome e namespace do `Element.tag`
        - `nome, namespace = self.__nome_namespace()`"""
        tag = self.__elemento.tag
        if tag.startswith("{") and "}" in tag:
            idx = tag.index("}")
            return (tag[idx + 1 :], tag[1 : idx])
        else: return (tag, None)

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
    def namespace (self) -> tipagem.url | None:
        """`Namespace` do elemento
        - Não leva em conta o `xmlns` do parente"""
        return self.__nome_namespace()[1]

    @namespace.setter
    def namespace (self, namespace: tipagem.url | None) -> None:
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
    def atributos (self) -> dict[str, tipagem.url]:
        """`Atributos` do elemento"""
        return self.__elemento.attrib

    @atributos.setter
    def atributos (self, valor: dict[str, tipagem.url]) -> None:
        """Setar `atributos`"""
        self.__elemento.attrib = valor

    def elementos (self) -> list[ElementoXML]:
        """Elementos filhos do elemento
        - Para remover ou adicionar elementos, utilizar as funções próprias"""
        return [
            ElementoXML.__from_element(elemento)
            for elemento in self.__elemento
        ]

    def encontrar (self, xpath: str, namespaces: dict[str, tipagem.url] = None) -> list[ElementoXML]:
        """Encontrar elementos que resultem no `xpath` informado
        - `xpath` deve retornar em elementos apenas, não em texto ou atributo
        - `namespaces` para utilizar prefixos no `xpath`, informar um dicionario { ns: url } ou registrar_prefixo()"""
        namespaces = namespaces or {}
        namespaces.update(self.__prefixos)
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
        return ElementoXML.parse(str(self))

    @staticmethod
    def registrar_prefixo (prefixo: str, namespace: tipagem.url) -> tipagem.url:
        """Registrar o `prefixo` para o determinado `namespace`
        - Retorna o `namespace`"""
        ElementoXML.__prefixos[prefixo] = namespace
        return register_namespace(prefixo, namespace) or namespace

    @classmethod
    def __from_element (cls, element: Element) -> ElementoXML:
        """Criação do `ElementoXML` diretamente com um `Element`"""
        elemento = cls.__new__(cls)
        elemento.__elemento = element
        return elemento

    @classmethod
    def parse (cls, xml: str) -> ElementoXML:
        """Parse do `xml` para um `ElementoXML`
        - `xml` pode ser uma string xml ou o caminho até o arquivo .xml"""
        xml = xml.lstrip() # remover espaços vazios no começo
        element = xml_from_string(xml) if xml.startswith("<") else xml_from_file(xml).getroot()
        return ElementoXML.__from_element(element)

__all__ = [
    "Json",
    "yaml_parse",
    "ElementoXML",
    "yaml_stringify"
]
