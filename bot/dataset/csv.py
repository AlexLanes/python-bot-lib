# std
import typing
# interno
from bot.estruturas import Caminho
from bot.formatos import Unmarshaller, decode
# externo opcional [dataset]
import polars

class Csv:
    """Classe para manipular arquivos `csv`
    - `caminho` deve terminar em `.csv`"""

    caminho: Caminho
    separador: str

    def __init__(self, caminho: Caminho | str, separador: str = ",") -> None:
        self.separador = separador
        self.caminho = Caminho(str(caminho))
        assert self.caminho.nome.endswith(".csv"), "Caminho deve terminar em '.csv'"
        self.caminho.parente.criar_diretorios()

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

    def escrever_dataframe (self, dataframe: "polars.DataFrame") -> Caminho:
        """Criar um arquivo csv no `self.caminho` com os dados informados do `dataframe`"""
        dataframe.write_csv(
            self.caminho.string,
            include_header = True,
            separator = self.separador
        )
        return self.caminho

    def ler (self) -> list[dict[str, typing.Any]]:
        """Ler o csv"""
        df = self.ler_dataframe()
        return decode(
            df.write_json(),
            decoder = "json",
            formato = list[dict[str, typing.Any]]
        )

    def ler_dataframe (self) -> "polars.DataFrame":
        """Ler o csv como um `polars.DataFrame`"""
        return polars.read_csv(
            self.caminho.string,
            separator = self.separador,
            raise_if_empty = False
        )

    def ler_unmarshal[T: Unmarshaller] (self, cls: type[T]) -> list[T]:
        """Ler o csv e realizar o unmarshal das linhas conforme a classe anotada `cls`
        ```python
        from bot.formatos import Unmarshaller

        class Registro (Unmarshaller):
            codigo: str
            descricao: str

        excel = bot.dataset.Csv("codigos.csv")
        registros = excel.ler_unmarshal(Registro)
        print(*registros, sep="\\n")
        ```"""
        return cls.UnmarshalMany(self.ler())

__all__ = ["Csv"]