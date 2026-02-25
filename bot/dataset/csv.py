# std
import typing
# interno
import bot
from bot.estruturas import Caminho
# externo
import polars

class Csv:
    """Classe para manipular arquivos `csv`
    - `caminho` deve terminar em `.csv`"""

    caminho: Caminho

    def __init__(self, caminho: Caminho | str) -> None:
        self.caminho = Caminho(str(caminho))
        assert self.caminho.nome.endswith(".csv"), "Caminho deve terminar em '.csv'"

    def escrever (self, dados: typing.Iterable[dict[str, typing.Any]]) -> Caminho:
        """Criar um arquivo csv no `self.caminho` com os `dados` informados
        ```python
        csv = bot.dataset.Csv("./exemplo.csv")
        caminho = csv.escrever([
            {"nome": "a", "valor": 1},
            {"nome": "b", "valor": 2}
        ])
        ```"""
        return self.escrever_dataframe(polars.DataFrame(dados))

    def escrever_dataframe (self, dataframe: polars.DataFrame, separador: str = ",") -> bot.sistema.Caminho:
        """Criar um arquivo csv no `self.caminho` com os dados informados do `dataframe`"""
        dataframe.write_csv(
            self.caminho.string,
            include_header = True,
            separator = separador
        )
        return self.caminho

    def ler (self) -> list[dict[str, typing.Any]]:
        """Ler o csv"""
        df = self.ler_dataframe()
        return (
            bot.formatos.Json
            .parse(df.write_json())
            .obter(list[dict[str, typing.Any]])
        )

    def ler_dataframe (self, separador: str = ",") -> polars.DataFrame:
        """Ler o csv como um `polars.DataFrame`"""
        return polars.read_csv(
            self.caminho.string,
            separator = separador,
            raise_if_empty = False
        )

    def ler_unmarshal[T] (self, cls: type[T]) -> list[T]:
        """Ler o csv e realizar o unmarshal das linhas conforme a classe `cls`
        ```python
        class Registro:
            codigo: str
            descricao: str
        excel = bot.dataset.Csv("codigos.csv")
        registros = excel.ler_unmarshal(Registro)
        print(*registros, sep="\\n")
        ```"""
        df = self.ler_dataframe()
        unmarshaller = bot.formatos.Unmarshaller(cls)
        return [
            unmarshaller.parse(item)
            for item in bot.formatos.Json
                .parse(df.write_json())
                .obter(list[dict[str, typing.Any]])
        ]

__all__ = ["Csv"]