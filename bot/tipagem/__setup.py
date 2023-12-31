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
parametrosSQL: TypeAlias = Iterable[nomeado] | Iterable[posicional]
"""Iterable de parâmetros utilizados quando for ser executado mais de 1 vez"""

char: TypeAlias = str
"""String com 1 caractere"""
email: TypeAlias = str
"""String formato E-mail"""

caminho: TypeAlias = str
"""Caminho relativo ou absoluto"""
caminhos: TypeAlias = list[str]
"""Lista de caminho relativo ou absoluto"""


DIRECOES_SCROLL = Literal["cima", "baixo"]
"""Direções de scroll do mouse"""
BOTOES_MOUSE = Literal["left", "middle", "right"]
"""Botões aceitos pelo `pynput`"""
PORCENTAGENS = Literal["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1"]
"""Porcentagens de confiança aceitos pelo `PyScreeze` e `EasyOCR`, entre 1.0 e 0.0"""
ESTRATEGIAS_WEBELEMENT = Literal["id", "xpath", "link text", "name", "tag name", "class name", "css selector", "partial link text"]
"""Estratégias para a localização de WebElements no `Selenium`"""
BOTOES_TECLADO = Literal["alt", "alt_l", "alt_r", "alt_gr", "backspace", "caps_lock", "cmd", "cmd_r", "ctrl", "ctrl_l", "ctrl_r", "delete", "down", "end", "enter", "esc", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19", "f20", "f21", "f22", "f23", "f24", "home", "left", "page_down", "page_up", "right", "shift", "shift_r", "space", "tab", "up", "media_play_pause", "media_volume_mute", "media_volume_down", "media_volume_up", "media_previous", "media_next", "insert", "menu", "num_lock", "pause", "print_screen", "scroll_lock"]
"""Botões especiais aceitos pelo `pynput`"""


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

    def __len__(self):
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
class ResultadoSQL:
    """Classe utilizada no retorno da execução do sqlite"""
    linhas_afetadas: int | None
    """Quantidade de linhas afetadas pelo comando sql
    - `None` indica que não se aplica para o comando sql"""
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
    uid: int
    """id do e-mail"""
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
    "char",
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
    "BOTOES_TECLADO",
    "DIRECOES_SCROLL",
    "ESTRATEGIAS_WEBELEMENT"
]
