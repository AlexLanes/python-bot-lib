import bot

HOST, USUARIO, REPOSITORIO, TOKEN = bot.configfile.obter_opcoes_obrigatorias("github", "host", "usuario", "repositorio", "token")

def apagar_release (id_release: int) -> None:
    response = bot.http.request(
        "DELETE",
        f"{HOST}/repos/{USUARIO}/{REPOSITORIO}/releases/{id_release}",
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }
    )
    assert response.status_code == 204

def criar_release (release: str) -> int:
    response = bot.http.request(
        "POST",
        f"{HOST}/repos/{USUARIO}/{REPOSITORIO}/releases",
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        },
        json = {
            "tag_name": release,
            "name": release,
        }
    )
    assert response.status_code == 201
    return response.json()["id"]

def obter_releases () -> dict[str, int]:
    """`{ Versão release: id release }`"""
    response = bot.http.request(
        "GET",
        f"{HOST}/repos/{USUARIO}/{REPOSITORIO}/releases",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }
    )

    releases, erro = bot.formatos.Json.parse(response.text)
    assert response.status_code == 200 and not erro and releases.validar({
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": { "type": "number" },
                "tag_name": { "type": "string" }
            }
        }
    }), "Erro ao obter os releases"

    return {
        release["tag_name"]: release["id"]
        for release in releases.valor()
        if release["tag_name"]
    }

def upload_asset (id_release: int, caminho_build: bot.sistema.Caminho) -> str:
    """retorna o url para a build"""
    host = HOST.replace("api", "uploads")
    response = bot.http.request(
        "POST",
        f"{host}/repos/{USUARIO}/{REPOSITORIO}/releases/{id_release}/assets",
        params = { "name": caminho_build.nome },
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/octet-stream"
        },
        content = open(caminho_build.string, "rb").read()
    )
    assert response.status_code == 201
    return response.json()["browser_download_url"]

def versao_build (caminho: bot.sistema.Caminho) -> str:
    return "v" + caminho.nome.removeprefix("bot-").removesuffix("-py3-none-any.whl")

def obter_ultima_build () -> bot.sistema.Caminho:
    return sorted(
        (c for c in bot.sistema.Caminho(".", "dist") if c.arquivo()),
        key = lambda c: c.nome,
        reverse = True
    )[0]

def main () -> None:
    sucesso, _ = bot.sistema.executar("build-script.bat")
    assert sucesso, "Falha ao executar o script de buid"
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