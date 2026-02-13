# std
from __future__ import annotations
import copy, datetime, types, tomllib, inspect
import json as jsonlib
from typing import Any, Generator, Literal, Self, get_args, get_origin, Union
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

class Json:
    """Classe para validação e leitura de itens JSON acessando propriedades via `.` ou `[]`
    - Conforme Javascript

    ### Exemplo
    ```
    item = {
        "nome": "Alex",
        "campo com espaço": 20,
        "documentos": { "cpf": "123", "rg": None, "cnpj": 1234567 },
        "enderecos": [{ "rua": "rua 1", "numero": 1 }, { "rua": "rua 2", "complemento": "próximo ao x" }],
    }

    # Criação
    json = Json.parse('{ "nome": "Alex" }')
    json = Json(item)

    # Caminhos válidos
    json.nome
    json["campo com espaço"]
    json.documentos.rg
    json.enderecos[0].rua

    # Caminhos invalidos
    json["errado"]
    json.enderecos[2]

    # Checar existência do caminho
    bool(json.nome)
    if json.nome: ...

    # Comparações aceitas
    json.nome == "Alex"
    json.nome != "Alex"
    "Alex" in json.nome # Usar em str, list e dict

    # Obter o tipo do json
    tipo = json.tipo()

    # Transformar para string json
    json.stringify(indentar=True)

    # Acessar o valor do `json` validando com o tipo `esperar`
    # Erro caso o caminho seja inválido ou o tipo `esperar` seja inválido
    valor = json.nome.obter(str)
    valor = json.nome.obter(str | None)
    valor = json["campo com espaço"].obter(Literal[20])
    valor = json.documentos.obter(dict)
    valor = json.enderecos.obter(list[dict[str, dict]])

    # Realizar o unmarshal do `item` conforme a `classe`
    objeto = json.unmarshal(classe)
    ```"""

    __item: Any
    """Representação JSON como objeto Python"""
    __valido: bool
    """Indicador se o caminho do json é valido"""
    __caminho: list[str]
    """Caminho percorrido"""

    def __init__ (self, item: Any) -> None:
        self.__item = item
        self.__valido = True
        self.__caminho = []

    @classmethod
    def parse (cls, json: str) -> Json:
        """Realiza o parse de uma string JSON na classe `Json`
        - `Exception` caso ocorra erro"""
        try: return Json(jsonlib.loads(json))
        except jsonlib.JSONDecodeError as erro:
            raise Exception(erro.msg)

    def __repr__ (self) -> str:
        """Representação da classe"""
        return f"<Json '{self.tipo().__name__ if self else "inválido"}'>"

    def __bool__ (self) -> bool:
        return self.__valido

    def __eq__ (self, value: object) -> bool:
        return self.__item == value

    def __contains__ (self, value: object) -> bool:
        try: return value in self.__item # type: ignore
        except Exception: return False

    def __getattr__ (self, chave: str) -> Json:
        """Obter o item filho de nome `chave`
        - Invalidado caso não encontrado"""
        json = self[chave]
        json.__caminho.pop(-1)
        json.__caminho.append(f".{chave}")
        return json

    def __getitem__ (self, value: int | str) -> Json:
        """Obter o item filho na posição `int` ou de nome `str`
        - Invalidado caso não encontrado"""
        try:
            json = Json(self.__item[value]) # type: ignore
        except Exception:
            json = Json(None)
            json.__valido = False

        json.__caminho.extend(self.__caminho)
        json.__caminho.append(f"[{value!r}]")
        return json

    def tipo (self) -> type:
        """Tipo do `json`"""
        return type(self.__item)

    def obter[T] (self, esperar: type[T] | Any) -> T:
        """Acessar o valor do `json` validando com o tipo `esperar`
        - Erro caso o caminho seja inválido ou o tipo `esperar` seja inválido
        - Tipos Esperados:
            - Primitivos `(str, int, float, bool, None)`
            - `Literal`
            - `|` `Union`
            - `dict`
            - `list`"""

        try:
            assert self
            return Unmarshaller(Unmarshaller).validar(esperar, self.__item)

        except Exception:
            caminho = "".join(["$", *self.__caminho])
            raise Exception(
                f"Erro {self!r} ao se obter o valor no Caminho({caminho}); "
                f"Esperado({esperar}) Encontrado({self.tipo()})"
            ) from None

    def unmarshal[T] (self, cls: type[T]) -> T:
        """Realizar o unmarshal do `item` conforme a classe `cls`
        - `item` do json deve ser um `dict`"""
        valor = self.obter(dict)
        return Unmarshaller(cls).parse(valor)

    def stringify (self, indentar: bool = False) -> str:
        """Transformar o item para o formato string"""
        def tratamentos (obj: Any) -> Any:
            if type(obj) in (int, float, str, bool, type(None)): return obj
            if isinstance(obj, datetime.datetime): return obj.isoformat(sep="T", timespec="seconds")
            if hasattr(obj, "__dict__"): return obj.__dict__
            if hasattr(obj, "__iter__"): return [tratamentos(item) for item in obj]
            if hasattr(obj, "__str__"): return obj.__str__()
            raise TypeError(f"Tipo inesperado para ser transformado em json: '{type(obj)}'")

        return jsonlib.dumps(
            self.__item,
            ensure_ascii = False,
            default = tratamentos,
            indent = 4 if indentar else None
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
    __prefixos: dict[str, bot.tipagem.url] = {}

    def __init__ (self, nome: str,
                        texto: str | None = None,
                        namespace: bot.tipagem.url | None = None,
                        atributos: dict[str, str] | None = None) -> None:
        nome = f"{{{namespace}}}{nome}" if namespace else nome
        self.__elemento = Element(nome, atributos or {})
        self.__elemento.text = texto

    @classmethod
    def parse (cls, xml: str | bot.sistema.Caminho) -> ElementoXML:
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
        return ElementoXML.parse(str(self))

    @staticmethod
    def registrar_prefixo (prefixo: str, namespace: bot.tipagem.url) -> bot.tipagem.url:
        """Registrar o `prefixo` para o determinado `namespace`
        - Retorna o `namespace`"""
        ElementoXML.__prefixos[prefixo] = namespace
        return register_namespace(prefixo, namespace) or namespace

class Unmarshaller[T]:
    """Classe para validação e parse de um `dict` para uma classe customizada
    - `__repr__` da classe alterada caso não tenha sido implementada
    - Propriedades são validadas como obrigatórios caso não possuam `Union` com `None` ou sem um default
    - Classes deve ter as propriedades e tipos devidamente anotados
    - Propriedades podem estar na versão normalizada `bot.util.normalizar`
    - Classes podem herdam propriedades de outras classes
    - Tipos Esperados:
        - Primitivos `(str, int, float, bool, None)`
        - `Literal`
        - `|` `Union`
        - `dict`
        - `list`
        - Alguma `class` seja do próprio Python ou uma classe com propriedades

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

    item = {
        "nome": "Alex",
        "idade": 27,
        "sexo": "M",
        "Informado Com Default": 20,
        "documentos": {"cpf": "123", "rg": None, "cnpj": 1234567 },
        "enderecos": [{ "rua": "rua 1", "numero": 1 }, { "rua": "rua 2", "complemento": "próximo ao x" }],
    }
    pessoa = Unmarshaller(Pessoa).parse(item)
    print(pessoa)
    ```
    """

    cls: type[T]
    PRIMITIVOS = (str, int, float, bool, types.NoneType)

    def __init__(self, cls: type[T]) -> None:
        # Confirmar classe
        assert inspect.isclass(cls) and cls.__module__ != "builtins",\
            f"Unmarshaller espera uma classe | Recebido({cls})"

        self.cls = cls
        if cls.__repr__ is object.__repr__:
            cls.__repr__ = lambda self: str(self.__dict__)

        # class attr escondido
        # gambiarra devido a classes como str: list["Classe"]
        # TODO talvez o python 3.14 resolva devido a alterações em tipagem futura
        if getattr(Unmarshaller, "cls_seen", None) == None:
            setattr(Unmarshaller, "cls_seen", {})

    def __repr__ (self) -> str:
        return f"<Unmarshaller[{self.cls.__name__}]>"

    def parse (self, item: dict[str, Any], **kwargs: str) -> T:
        """Realizar o parse do `item` conforme a classe informada"""
        obj = object.__new__(self.cls)
        caminho = kwargs.get("caminho", "$")
        chaves_normalizadas = {
            bot.util.normalizar(chave): chave
            for chave in item.keys()
        }

        for nome, tipo in self.coletar_anotacoes_classe().items():
            caminho_atual = f"{caminho}.{nome}" if caminho else nome
            valor_item = item.get(
                # nome exato ou procurado pela versão normalizada
                nome if nome in item else chaves_normalizadas.get(nome, nome),
                # checar por default da propriedade e obter uma cópia do valor
                copy.deepcopy(getattr(obj, nome, None))
            )
            setattr(obj, nome, self.validar(tipo, valor_item, caminho_atual))

        return obj

    def coletar_anotacoes_classe (self) -> dict[str, type]:
        base_e_parentes = {}
        for cls in reversed(self.cls.__mro__):
            base_e_parentes.update(getattr(cls, '__annotations__', {}))
        return base_e_parentes

    def validar[V] (self, esperar: type | Any, valor: V, caminho: str = "") -> V:
        """Validar se o `valor` de acordo com o tipo `esperar` e retornar o `valor`
        - Erro caso o `valor` não possuao tipo `esperar`"""
        if isinstance(esperar, str):
            esperar = Unmarshaller.cls_seen.get(esperar, esperar) # type: ignore

        # Any ou mesmo tipo
        if esperar is Any or esperar is type(valor):
            return valor

        # primitivos
        if any(esperar is t and isinstance(valor, t)
               for t in self.PRIMITIVOS):
            return valor

        origin = get_origin(esperar)

        # Class
        if hasattr(esperar, '__annotations__'):
            if not isinstance(valor, dict):
                raise self.criar_erro(caminho, dict, valor)
            if esperar.__name__ not in Unmarshaller.cls_seen: # type: ignore
                Unmarshaller.cls_seen[esperar.__name__] = esperar # type: ignore
            return Unmarshaller(esperar).parse(valor, caminho=caminho)

        # Literal
        if origin is Literal:
            expected_values = get_args(esperar)
            if expected_values and valor not in expected_values:
                raise self.criar_erro(caminho, Literal[expected_values], valor)
            return valor

        # Union
        if origin in (types.UnionType, Union):
            for t in get_args(esperar):
                try: return self.validar(t, valor, caminho)
                except Exception: pass

        # list
        if esperar is list or origin is list:
            item_type, *_ = get_args(esperar) or [Any]
            if not isinstance(valor, list):
                raise self.criar_erro(caminho, list, valor)
            return [
                self.validar(item_type, v, f"{caminho}[{i}]")
                for i, v in enumerate(valor)
            ] # type: ignore

        # dict
        if esperar is dict or origin is dict:
            key_type, val_type = get_args(esperar) or (str, Any)
            if key_type is not str:
                raise NotImplementedError("Apenas dict[str, V] é suportado.")
            if not isinstance(valor, dict):
                raise self.criar_erro(caminho, dict, valor)
            return {
                k: self.validar(val_type, v, f"{caminho}.{k}")
                for k, v in valor.items()
            } # type: ignore

        raise self.criar_erro(caminho, esperar, valor)

    def criar_erro (self, caminho: str, esperado: Any, valor: Any) -> Exception:
        return Exception(
            f"Erro {repr(self).strip("<>")} no Caminho({caminho}) "
            f"Esperado({esperado}) "
            f"Encontrado({type(valor)}) Valor({valor})"
        )

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

    def __init__ (self, caminho: str | bot.sistema.Caminho) -> None:
        caminho = bot.sistema.Caminho(str(caminho))
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

    def obter[T] (self, chave: str, tipo: type[T] | Any = str) -> T:
        """Obter a `chave` e esperar o `tipo`
        - Erro caso a `chave` não exista ou o `tipo` for inválido
        - Alternativa `toml[chave]` que não faz validação do `tipo`"""
        valor = self[chave]
        try: return Unmarshaller(Unmarshaller).validar(tipo, valor)
        except Exception: raise ValueError(
            f"Falha ao obter a chave '{chave}' no Toml; "
            f"Tipo esperado {tipo} incompatível com {type(valor)}"
        ) from None

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