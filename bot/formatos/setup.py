# std
from __future__ import annotations
from types import UnionType, NoneType
from typing import Any, Generator, Literal, Self, get_args, get_origin
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
from .. import tipagem, sistema
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

    @classmethod
    def parse (cls, json: str) -> tuple[Json, str | None]:
        """Realiza o parse de uma string JSON na classe `Json`
        - retorno `(Json, None) ou (Json vazio, mensagem de erro)`"""
        try: return Json(json_parse(json)), None
        except JSONDecodeError as erro:
            return Json({}), erro.msg

    def __repr__ (self) -> str:
        """Representação da classe"""
        tipo = self.tipo().__name__
        return f"<Json [{tipo}]>"

    def __bool__ (self) -> bool:
        """Indicador se o caminho percorrido no `json` é valido"""
        return self.__valido

    def __getattr__ (self, chave: str) -> Json:
        return self[chave]

    def __getitem__ (self, value: int | str) -> Json:
        """Obter o item filho na posição `int` ou elemento de nome `str`
        - Invalidar o `json` se o caminho for invalido"""
        try:
            if self.tipo() in (list, tuple, dict):
                return Json(self.__item[value]) # type: ignore

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
        return value in self.valor() if self.tipo() in (list, tuple, dict, str) else False # type: ignore

    def tipo (self) -> type[T]:
        """Tipo raiz do `json`"""
        return type(self.__item)

    def valor (self) -> T:
        """Valor raiz do `json`"""
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

    def validar (self, schema: dict[str, Any]) -> tuple[bool, None | str]:
        """Validar se o `json` está de acordo com o `schema`
        - retorno `(sucesso, None ou mensagem de erro)`"""
        try: return validate_schema(self.__item, schema) == None, None
        except SchemaError as erro:
            return False, f"Schema para validação apresentou o erro: {erro.message}"
        except ValidationError as erro:
            return False, f"Erro de validação: {erro.message}"

    def unmarshal[C] (self, cls: type[C]) -> tuple[C, None | str]:
        """Realizar o parse dos `Json` conforme a classe `cls`
        - retorno `(instancia preenchida corretamente, None) ou (instancia vazia, mensagem de erro)`"""
        valor = self.valor()
        return Unmarshaller(cls).parse(valor) if isinstance(valor, dict) else (
            object.__new__(cls),
            f"Json deve ser do tipo 'dict' para ser feito o unmarshal e não tipo '{self.tipo()}'"
        )

class ElementoXML:
    """Classe de manipulação de XML
    - Abstração do módulo `xml.etree.ElementTree`"""

    __elemento: Element
    __prefixos: dict[str, tipagem.url] = {}

    def __init__ (self, nome: str,
                        texto: str | None = None,
                        namespace: tipagem.url | None = None,
                        atributos: dict[str, str] | None = None) -> None:
        nome = f"{{{namespace}}}{nome}" if namespace else nome
        self.__elemento = Element(nome, atributos or {})
        self.__elemento.text = texto

    @classmethod
    def parse (cls, xml: str | sistema.Caminho) -> ElementoXML:
        """Parse do `xml` para um `ElementoXML`
        - `xml` pode ser uma string xml ou o caminho até o arquivo .xml"""
        xml = str(xml).lstrip() # remover espaços vazios no começo
        element = xml_from_string(xml) if xml.startswith("<") else xml_from_file(xml).getroot()
        return ElementoXML.__from_element(element)

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
        """Iterator dos `elementos`"""
        for elemento in self.elementos():
            yield elemento

    def __bool__ (self) -> bool:
        """Formato `bool`"""
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
    def atributos (self) -> dict[str, str]:
        """`Atributos` do elemento"""
        return self.__elemento.attrib

    @atributos.setter
    def atributos (self, valor: dict[str, str]) -> None:
        """Setar `atributos`"""
        self.__elemento.attrib = valor

    def __nome_namespace (self) -> tuple[str, tipagem.url | None]:
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

    def encontrar (self, xpath: str, namespaces: dict[str, tipagem.url] | None = None) -> list[ElementoXML]:
        """Encontrar elementos que resultem no `xpath` informado
        - `xpath` deve retornar em elementos apenas, não em texto ou atributo
        - `namespaces` para utilizar prefixos no `xpath`, informar um dicionario { ns: url } ou registrar_prefixo()"""
        namespaces = namespaces.copy() if namespaces else {}
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

class UnmarshalError (Exception):
    def __init__ (self, path: str, expected: Any, value: Any) -> None:
        super().__init__(
            f"Erro ao processar '{path}'; Esperado {expected}; Encontrado {type(value)} {value}"
        )

    @classmethod
    def from_message (cls, message: str) -> UnmarshalError:
        obj = cls.__new__(cls)
        super(UnmarshalError, obj).__init__(message)
        return obj

class Unmarshaller[T]:
    """Classe para validação e parse de um `dict` para uma classe customizada
    - `__repr__` da classe alterada caso não tenha sido implementada
    - Propriedades são validadas como obrigatórios caso não possuam `Union` com `None` ou sem um default
    - Classes deve ter as propriedades e tipos devidamente anotados
    - Classes podem herdam propriedades de outras classes
    - Tipos Esperados:
        - Primitivos
        - Literal
        - Union |
        - dict
        - list
        - class

    ```
    # Classes de exemplo
    class Endereco:
        rua: str
        numero: int | None
    class EnderecoComComplemento (Endereco):
        complemento: str
    class Pessoa:
        nome: str
        idade: int
        sexo: Literal["M", "F"]
        opcional: str | None
        opcional_com_default: str = "default"
        informado_com_default: int | str = "10"
        documentos: dict[str, str | int | None]
        enderecos: list[Endereco | EnderecoComComplemento]

    item, erro = Unmarshaller(Pessoa).parse({
        "nome": "Alex",
        "idade": 27,
        "sexo": "M",
        "informado_com_default": 20,
        "documentos": {"cpf": "123", "rg": None, "cnpj": 1234567 },
        "enderecos": [{ "rua": "rua 1", "numero": 1 }, { "rua": "rua 2", "complemento": "próximo ao x" }],
    })
    assert not erro, f"Falha no unmarshal: {erro}"
    print(item)
    ```
    """

    __cls: type[T]
    __primitives = (str, int, float, bool, NoneType)

    def __init__(self, cls: type[T]) -> None:
        self.__cls = cls
        if cls.__repr__ is object.__repr__:
            cls.__repr__ = lambda self: str(self.__dict__)

        # class attr escondido
        # gambiarra devido a classes como str: list["Classe"]
        # TODO talvez o python 3.14 resolva devido a alterações em tipagem futura
        if getattr(Unmarshaller, "cls_seen", None) == None:
            setattr(Unmarshaller, "cls_seen", {})

    def __repr__ (self) -> str:
        return f"<Unmarshaller[{self.__cls.__name__}]>"

    def parse (self, item: dict[str, Any], **kwargs: str) -> tuple[T, str | None]:
        """Realizar o parse do `item` conforme a classe informada
        - `(instancia preenchida corretamente, None)`
        - `(instancia incompleta, mensagem de erro)`"""
        erro: str | None = None
        obj = object.__new__(self.__cls)        
        path = kwargs.get("path", "") or self.__cls.__name__

        try:
            for name, t in self.__collect_annotations().items():
                current_path = f"{path}.{name}" if path else name
                default = getattr(obj, name, None)
                value = item.get(name, default)
                setattr(obj, name, self.__validate(t, value, current_path))

        except UnmarshalError as e:
            erro = str(e)

        return obj, erro

    def __collect_annotations (self) -> dict[str, type]:
        base_and_parent_annotations = {}
        for cls in reversed(self.__cls.__mro__):
            base_and_parent_annotations.update(getattr(cls, '__annotations__', {}))
        return base_and_parent_annotations

    def __validate (self, expected: type | Any, value: Any, path: str) -> Any:
        if isinstance(expected, str):
            expected = Unmarshaller.cls_seen.get(expected, expected) # type: ignore

        origin = get_origin(expected)

        # any
        if expected is Any:
            return value

        # primitivo
        if any(expected is t and isinstance(value, t)
               for t in self.__primitives):
            return value

        # class
        if hasattr(expected, '__annotations__'):
            if not isinstance(value, dict):
                raise UnmarshalError(path, dict, value)
            if expected.__name__ not in Unmarshaller.cls_seen: # type: ignore
                Unmarshaller.cls_seen[expected.__name__] = expected # type: ignore
            value, nok = Unmarshaller(expected).parse(value, path=path)
            if nok: raise UnmarshalError.from_message(nok)
            return value

        # literal
        if origin is Literal:
            expected_values = get_args(expected)
            if expected_values and value not in expected_values:
                raise UnmarshalError(path, Literal[expected_values], value)
            return value

        # union
        if origin is UnionType:
            for t in get_args(expected):
                try: return self.__validate(t, value, path)
                except Exception: pass

        # list
        if expected is list or origin is list:
            item_type, *_ = get_args(expected) or [Any]
            if not isinstance(value, list):
                raise UnmarshalError(path, list, value)
            return [
                self.__validate(item_type, v, f"{path}[{i}]")
                for i, v in enumerate(value)
            ]

        # dict
        if expected is dict or origin is dict:
            key_type, val_type = get_args(expected) or (str, Any)
            if key_type is not str:
                raise NotImplementedError("Apenas dict[str, V] é suportado.")
            if not isinstance(value, dict):
                raise UnmarshalError(path, dict, value)
            return {
                k: self.__validate(val_type, v, f"{path}.{k}")
                for k, v in value.items()
            }

        raise UnmarshalError(path, expected, value)

__all__ = [
    "Json",
    "yaml_parse",
    "ElementoXML",
    "Unmarshaller",
    "yaml_stringify"
]