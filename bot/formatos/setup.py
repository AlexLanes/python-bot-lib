# std
from __future__ import annotations
import copy, tomllib
from types import UnionType, NoneType
from json import JSONDecodeError, dumps as json_dumps, loads as json_parse
from typing import Any, Generator, Literal, Self, get_args, get_origin, Union
from xml.etree.ElementTree import (
    Element,
    register_namespace,
    indent as indentar_xml,
    parse as xml_from_file,
    tostring as xml_to_string,
    fromstring as xml_from_string,
)
# interno
from .. import tipagem, sistema, util
# externo
from jsonschema import (
    SchemaError,
    ValidationError,
    validate as validate_schema
)

class Json [T]:
    """Classe para validação e leitura de objetos JSON acessando propriedades via `.` ou `[]`

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
    """Classe de manipulação e criação de XML
    - Abstração do módulo `xml.etree.ElementTree`

    ```
    # Parse
    ElementoXML.parse(bot.sistema.Caminho("arquivo.xml"))
    ElementoXML.parse('<raiz versão="1"><filho1>abc</filho1><filho2>xyz</filho2></raiz>')

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

    def encontrar (self, xpath: str, namespaces: dict[str, tipagem.url] | None = None) -> ElementoXML | None:
        """Encontrar elemento que resulte no `xpath` informado ou `None` caso não seja encontrado
        - `xpath` deve retornar no elemento apenas, não em texto ou atributo
        - `namespaces` para utilizar prefixos no `xpath`, informar um dicionario `{ ns: url } ou registrar_prefixo()`"""
        p = self.__prefixos
        namespaces = { **namespaces, **p } if namespaces else p
        xpath = xpath if xpath.startswith(".") else f".{xpath}"
        elemento = self.__elemento.find(xpath, namespaces)
        return ElementoXML.__from_element(elemento) if elemento != None else None

    def procurar (self, xpath: str, namespaces: dict[str, tipagem.url] | None = None) -> list[ElementoXML]:
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
    - Propriedades podem estar na versão normalizada `bot.util.normalizar`
    - Classes podem herdam propriedades de outras classes
    - Tipos Esperados:
        - Primitivos
        - Literal
        - Union |
        - dict
        - list
        - class

    ```
    from bot.formatos import Unmarshaller
    from typing import Literal

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
        "Informado Com Default": 20,
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
        caminho = kwargs.get("path", "") or self.__cls.__name__
        chaves_normalizadas = {
            util.normalizar(chave): chave
            for chave in item.keys()
        }

        try:
            for nome, tipo in self.__coletar_anotacoes_classe().items():
                caminho_atual = f"{caminho}.{nome}" if caminho else nome
                valor_item = item.get(
                    # nome exato ou procurado pela versão normalizada
                    nome if nome in item else chaves_normalizadas.get(nome, nome),
                    # checar por default da propriedade e obter uma cópia do valor
                    copy.deepcopy(getattr(obj, nome, None))
                )
                setattr(obj, nome, self.__validate(tipo, valor_item, caminho_atual))

        except UnmarshalError as e:
            erro = str(e)

        return obj, erro

    def __coletar_anotacoes_classe (self) -> dict[str, type]:
        base_e_parentes = {}
        for cls in reversed(self.__cls.__mro__):
            base_e_parentes.update(getattr(cls, '__annotations__', {}))
        return base_e_parentes

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
        if origin in (UnionType, Union):
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

class Toml:
    """Classe para leitura, acesso e validação de tipo do formato `TOML`
    - O formato toml aceita os tipos: `str, int, float, bool, dict[str, ...], list[...]`
    - `chave` aceita chaves aninhadas. Exemplo `tool."setup tools"`

    ```
    toml = Toml("arquivo.toml")
    chave = 'tool."setuptools"'
    # Checar existência
    chave in toml
    toml.existe(chave)
    # Obter valor sem validação
    toml[chave]
    # Obter valor com validação
    toml.obter(chave, dict[str, str | int])
    ```
    """

    dados: dict[str, Any]
    """Dados raiz do `toml`"""

    def __init__ (self, caminho: str | sistema.Caminho) -> None:
        caminho = sistema.Caminho(str(caminho))
        self.dados = tomllib.loads(caminho.path.read_text(encoding="utf-8"))

    def __repr__ (self) -> str:
        return f"<bot.formatos.Toml>"

    def __contains__ (self, chave: object) -> bool:
        if not isinstance(chave, str):
            raise ValueError(f"Chave deve ser 'str' | Recebido '{chave}'")

        dados = self.dados
        for chave in self.__parse_chaves_aninhadas(chave):
            if not (isinstance(dados, dict) and chave in dados):
                return False
            dados = dados[chave]

        return True

    def __getitem__ (self, chave: object) -> Any:
        if not isinstance(chave, str):
            raise ValueError(f"Chave deve ser 'str' | Recebido '{chave}'")

        dados = self.dados
        for chave in self.__parse_chaves_aninhadas(chave):
            if not (isinstance(dados, dict) and chave in dados):
                raise KeyError(f"Chave '{chave}' não encontrada no Toml")
            dados = dados[chave]

        return dados

    def existe (self, chave: str) -> bool:
        """Checar se a `chave` existe
        - Alternativa ao operador `in`"""
        return chave in self

    def obter[T] (self, chave: str, tipo: type[T] = str) -> T:
        """Obter a `chave` e esperar o `tipo`
        - Erro caso a `chave` não exista ou o `tipo` for inválido
        - Alternativa `toml[chave]` não faz validação do `tipo`"""
        valor = self[chave]
        if not self.__validar_tipo(valor, tipo):
            raise ValueError(f"Falha ao obter a chave '{chave}' no Toml | Tipo do valor incompatível com tipo '{tipo}'")
        return valor

    def __validar_tipo[T] (self, valor: Any, tipo: type[T]) -> bool:
        origem = get_origin(tipo)

        # Any
        if tipo is Any: return True
        # primitivos
        if origem is None: return isinstance(valor, tipo)

        # union
        if origem in (UnionType, Union):
            return any(self.__validar_tipo(valor, t)
                       for t in get_args(tipo))

        # list
        if tipo is list or origem is list:
            tipo_item, *_ = get_args(tipo) or [Any]
            if not isinstance(valor, list):
                return False
            return all(
                self.__validar_tipo(item, tipo_item)
                for item in valor
            )

        # dict
        if tipo is dict or origem is dict:
            tipo_chave, tipo_valor = get_args(tipo) or (str, Any)
            if tipo_chave is not str or not isinstance(valor, dict):
                return False
            return all(
                self.__validar_tipo(v, tipo_valor)
                for v in valor.values()
            )

        return False

    def __parse_chaves_aninhadas (self, chave: str) -> list[str]:
        em_aberto, chaves = False, list[str]()
        for parte in chave.split("."):
            if not em_aberto:
                em_aberto = parte.startswith('"')
                chaves.append(parte.lstrip('"'))
                continue

            fechando = parte.endswith('"')
            chaves[-1] += f".{parte.rstrip('"')}"
            em_aberto = not fechando

        return chaves

__all__ = [
    "Toml",
    "Json",
    "ElementoXML",
    "Unmarshaller",
]