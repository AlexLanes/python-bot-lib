# std
from dataclasses import dataclass
from csv import writer as CsvWriter
from datetime import datetime as DateTime
from typing import Literal, Generator, TypeAlias, Iterable
# externo
from pandas import DataFrame


tiposSQL: TypeAlias = str | int | float | None
"""Tipos primitivos aceitos pelo sql"""
nomeado: TypeAlias = dict[str, tiposSQL]
"""Parâmetros necessários quando o SQL é nomeado ':nome'"""
posicional: TypeAlias = Iterable[tiposSQL]
"""Parâmetros necessários quando o SQL é posicionail '?'"""
parametrosSQL: TypeAlias = Iterable[nomeado | posicional]
"""Iterabela de parâmetros utilizados quando for ser executado mais de 1 vez"""


email: TypeAlias = str
"""String formato E-mail"""
caminho: TypeAlias = str
"""Caminho relativo ou absoluto"""
caminhos: TypeAlias = list[str]
"""Lista de caminho relativo ou absoluto"""


DIRECOES_SCROLL = Literal["cima", "baixo"]
"""Direções do scroll do mouse"""
BOTOES_MOUSE = Literal["left", "middle", "right"]
"""Botões aceitos pelo `PyAutoGui`"""
PORCENTAGENS = Literal["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1"]
"""Porcentagens de confiança aceitos pelo `PyAutoGui` e `EasyOCR`, entre 1.0 e 0.0"""
ESTRATEGIAS_WEBELEMENT = Literal["id", "xpath", "link text", "name", "tag name", "class name", "css selector", "partial link text"]
"""Estratégias para a localização de WebElements no `Selenium`"""
BOTOES_TECLADO = Literal['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', 'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace', 'browserback', 'browserfavorites', 'browserforward', 'browserhome', 'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear', 'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete', 'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20', 'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja', 'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail', 'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack', 'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn', 'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn', 'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator', 'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab', 'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen', 'command', 'option', 'optionleft', 'optionright']
"""Botões aceitos pelo `PyAutoGui`"""


@dataclass
class InfoStack:
    """Informações retiradas do Stack de execução"""
    nome: str
    """Nome arquivo"""
    caminho: caminho
    """Caminho arquivo"""
    funcao: str
    """Nome da função"""
    linha: int
    """Linha do item executado"""


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
    
    def transformar (self, xOffset=0.5, yOffset=0.5) -> tuple[int, int]:
        """Transformar as cordenadas para a posição (X, Y) de acordo com a porcentagem `xOffset` e `yOffset`
        - (X, Y) central caso os offsets não tenham sido informados
        - `xOffset` esquerda, centro, direita = 0.0, 0.5, 1.0
        - `yOffset` topo, centro, baixo = 0.0, 0.5, 1.0"""
        # enforça o range entre 0.0 e 1.0
        xOffset, yOffset = max(0.0, min(1.0, xOffset)), max(0.0, min(1.0, yOffset))
        return (self.x + int(self.largura * xOffset), 
                self.y + int(self.altura * yOffset))

    def __len__(self):
        return 4


@dataclass
class Diretorio:
    """Armazena os caminhos de pastas e arquivos presentes no diretório"""
    caminho: caminho
    """Caminho absoluto do diretorio"""
    pastas: caminhos
    """Lista contendo o caminho de cada pasta do diretório"""
    arquivos: caminhos
    """Lista contendo o caminho de cada arquivo do diretório"""


@dataclass 
class TextoCoordenada:
    """Item extraído pelo LeitorOCR"""
    texto: str
    """Texto extraído pelo OCR"""
    coordenada: Coordenada
    """Coordenada do texto"""


@dataclass
class FrequenciaCor:
    """Armazena a cor e a quantidade que a cor apareceu na imagem/tela"""
    frequencia: int
    """Quantidade de pixeis contendo a cor"""
    cor: tuple[int, int, int]
    """Cor (R, G, B)"""


@dataclass
class ResultadoSQL:
    """Classe utilizada no retorno da execução do sqlite"""
    qtd_linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql (None indica que não se aplica para o comando sql)"""
    colunas: list[str]
    """Colunas das linhas retornadas (se houver)"""
    linhas: Generator[list, None, None]
    """Generator das linhas retornadas (se houver)"""

    def __iter__ (self) -> Generator[list, None, None]:
        """Generator do self.linhas"""
        for linha in self.linhas: yield linha
    
    def to_dataframe (self) -> DataFrame:
        """Salvar o resultado em um pandas DataFrame"""
        return DataFrame(self, columns=self.colunas)

    def to_csv (self, caminho="resultado.csv") -> None:
        """Salvar o resultado em um arquivo .csv
        - `caminho` pode conter o caminho que será salvo o arquivo. Pode conter o caminho + nome do arquivo + .csv ao fim"""
        assert caminho.endswith(".csv"), "Caminho do arquivo deve terminar em '.csv'"
        with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
            writer = CsvWriter(arquivo)
            writer.writerow(self.colunas) # nome das colunas
            writer.writerows(self.linhas) # linhas


@dataclass
class Email:
    """Classe para armazenar informações extraídas de Email"""
    remetente: email
    """Remetente que enviou o e-mail"""
    destinatarios: list[email]
    """Destinatários que receberam o e-mail"""
    assunto: str
    """Assunto do e-mail"""
    data: DateTime
    """Data de envio do e-mail"""
    texto: str | None
    """Conteúdo do e-mail como texto"""
    html: str | None
    """Conteúdo do e-mail como html"""
    anexos: list[tuple[str, str, int, bytes]]
    """Anexos do e-mail
    - `for (nome, tipo, tamanho, conteudo) in email.anexos:`"""


__all__ = [
    "email",
    "Email",
    "nomeado",
    "caminho",
    "caminhos",
    "tiposSQL",
    "InfoStack",
    "Diretorio",
    "Coordenada",
    "posicional",
    "BOTOES_MOUSE",
    "PORCENTAGENS",
    "ResultadoSQL",
    "parametrosSQL",
    "FrequenciaCor",
    "BOTOES_TECLADO",
    "DIRECOES_SCROLL",
    "TextoCoordenada",
    "ESTRATEGIAS_WEBELEMENT"
]
