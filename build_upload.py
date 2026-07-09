# interno
import bot
from bot.formatos import Unmarshaller

HOST, USUARIO, REPOSITORIO, TOKEN = bot.config.github.obter("host", "usuario", "repositorio", "token")

class Project (Unmarshaller, rename="kebab"):
    requires_python: str
    dependencies: list[str]
    optional_dependencies: dict[str, list[str]]
class PyProject (Unmarshaller):
    project: Project

def apagar_release (id_release: int) -> None:
    (
        bot.http.request(
            "DELETE",
            f"{HOST}/repos/{USUARIO}/{REPOSITORIO}/releases/{id_release}",
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {TOKEN}"
            }
        )
        .esperar_status_code(204)
    )

def obter_descricao_release () -> str:
    caminho = bot.sistema.Caminho("./pyproject.toml")
    project = PyProject.Decode(caminho).project
    pacotes = [caminho.nome
               for caminho in bot.sistema.Caminho("./bot")
               if caminho.diretorio() and not caminho.nome.startswith("__")]
    return "<br>".join((
        f"**Python:** {project.requires_python!r}",
        f"**Pacotes:** {pacotes!r}",
        f"**Dependências:** {project.dependencies!r}",
        f"**Opcionais:** {project.optional_dependencies!r}",
    ))

def criar_release (release: str) -> int:
    class Retorno (Unmarshaller):
        id: int

    return (
        bot.http.request(
            "POST",
            f"{HOST}/repos/{USUARIO}/{REPOSITORIO}/releases",
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {TOKEN}"
            },
            json = {
                "tag_name": release,
                "name": release,
                "body": obter_descricao_release(),
            }
        )
        .esperar_status_code(201)
        .unmarshal(Retorno)
        .id
    )

def obter_releases () -> dict[str, int]:
    """`{ Versão release: id release }`"""
    class Release (Unmarshaller):
        id: int
        tag_name: str | None = None

    releases = (
        bot.http.request(
            "GET",
            f"{HOST}/repos/{USUARIO}/{REPOSITORIO}/releases",
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {TOKEN}"
            }
        )
        .esperar_status_code(200)
        .unmarshal_many(Release)
    )

    return {
        release.tag_name: release.id
        for release in releases
        if release.tag_name
    }

def upload_asset (id_release: int, caminho_build: bot.sistema.Caminho) -> str:
    """retorna o url para a build"""
    class Retorno (Unmarshaller):
        browser_download_url: str

    host = HOST.replace("api", "uploads")
    return (
        bot.http.request(
            "POST",
            f"{host}/repos/{USUARIO}/{REPOSITORIO}/releases/{id_release}/assets",
            query = { "name": caminho_build.nome },
            headers = {
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/octet-stream"
            },
            conteudo = open(caminho_build.string, "rb").read()
        )
        .esperar_status_code(201)
        .unmarshal(Retorno)
        .browser_download_url
    )

def versao_build (caminho: bot.sistema.Caminho) -> str:
    versão = caminho.nome.split("-")[1]
    return f"v{versão}"

def obter_ultima_build () -> bot.sistema.Caminho:
    arquivos_whl = [c for c in bot.sistema.Caminho(".", "dist")
                    if c.arquivo() and c.nome.endswith(".whl")]
    assert arquivos_whl, "Nenhuma build '.whl' encontrada em './dist'"
    return sorted(arquivos_whl, key=lambda c: c.nome, reverse=True)[0]

def main () -> None:
    sucesso, erro = bot.sistema.executar("uv", "build",  "--wheel")
    assert sucesso, f"Falha ao executar o script de build\n{erro}"

    caminho = obter_ultima_build()
    print(f"\n### Build gerada com sucesso: {caminho} ###")

    release = versao_build(caminho)
    print(f"### Release: {release} ###")

    releases = obter_releases()
    if release in releases:
        id_release = releases[release]
        apagar_release(id_release)
        print(f"### Release existente, id {id_release}, foi apagado ###")

    id_release = criar_release(release)
    print(f"### Criado release id: {id_release} ###")

    url_download = upload_asset(id_release, caminho)
    print(f"### Build da versão {release} criada e realizado upload com sucesso para o GitHub ###")
    print(f"### Url para a build: {url_download} ###\n")

if __name__ == "__main__":
    main()