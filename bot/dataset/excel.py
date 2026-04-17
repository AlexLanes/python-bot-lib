# std
import typing
# interno
import bot
from bot.estruturas import Resultado, Caminho
# externo
import polars
from xlsxwriter import Workbook
from fastexcel import read_excel

@Resultado.decorador
def escapar_tag_xml (df: polars.DataFrame) -> polars.DataFrame:
    return df.select([
        polars.col(col)
            .str.replace_all("<", "&lt;")
            .str.replace_all(">", "&gt;")
        if df.schema[col] == polars.String
        else polars.col(col)

        for col in df.columns
    ])

class Excel:
    """Classe para manipular arquivos `excel`
    - `caminho` deve terminar em `.xlsx`"""

    caminho: Caminho

    def __init__ (self, caminho: Caminho | str) -> None:
        self.caminho = Caminho(str(caminho))
        assert self.caminho.nome.endswith(".xlsx"), "Caminho deve terminar em '.xlsx'"
        self.caminho.parente.criar_diretorios()

    def escrever (self, **planilhas: typing.Iterable[dict[str, typing.Any]]) -> Caminho:
        """Criar um arquivo excel no `self.caminho` com os dados informados de `planilhas`
        ```python
        excel = bot.dataset.Excel("./exemplo.xlsx")
        caminho = excel.escrever(
            planilha1 = [{"nome": "a", "valor": 1}, {"nome": "b", "valor": 2}],
            planilha2 = [{"codigo": "a", "descricao": ""}, {"codigo": "b", "descricao": ""}],
        )
        ```"""
        return self.escrever_dataframe({
            nome: polars.DataFrame(dados)
            for nome, dados in planilhas.items()
        })

    def escrever_dataframe (self, planilhas: dict[str, polars.DataFrame]) -> Caminho:
        """Criar um arquivo excel no `self.caminho` com os dados informados em `planilhas`
        - `planilhas` sendo `{ nome_planilha: polars.Dataframe }`"""
        with Workbook(self.caminho.string) as excel:
            for nome_planilha, df in planilhas.items():
                df = escapar_tag_xml(df).valor_ou(df)
                df.write_excel(excel, nome_planilha, autofit=True)

        return self.caminho

    @property
    def planilhas (self) -> list[str]:
        """Nome das planilhas do excel"""
        return read_excel(self.caminho.path).sheet_names

    def ler_planilha (self, planilha: str | None = None) -> list[dict[str, typing.Any]]:
        """Ler a `planilha` do excel
        - `planilha=None` primeira planilha"""
        df = self.ler_dataframe(planilha)
        return (
            bot.formatos.Json
            .parse(df.write_json())
            .obter(list[dict[str, typing.Any]])
        )

    def ler_planilhas (self) -> dict[str, list[dict[str, typing.Any]]]:
        """Ler as planilhas do excel
        - Retorno formato `{ nome_planilha: [{...}] }`"""
        return {
            planilha: self.ler_planilha(planilha)
            for planilha in self.planilhas
        }

    def ler_dataframe (self, planilha: str | None = None) -> polars.DataFrame:
        """Ler a `planilha` do excel como um `polars.DataFrame`
        - `planilha=None` primeira planilha"""
        return polars.read_excel(
            self.caminho.string,
            sheet_name = planilha,
            raise_if_empty = False,
        )

    def ler_unmarshal[T] (self, cls: type[T], planilha: str | None = None) -> list[T]:
        """Ler a `planilha` do excel e realizar o unmarshal das linhas conforme a classe anotada `cls`
        - `planilha=None` primeira planilha
        ```python
        class Registro:
            codigo: str
            descricao: str
        excel = bot.dataset.Excel("codigos.xlsx")
        registros = excel.ler_unmarshal(Registro)
        print(*registros, sep="\\n")
        ```"""
        return (
            bot.formatos.Json
            .parse(self.ler_dataframe(planilha).write_json())
            .unmarshal(list[cls])
        )

__all__ = ["Excel"]