import bot

HOST, TOKEN = bot.configfile.obter_opcoes("github", ["host", "token"])

def criar_release (release: str) -> int:
    response = bot.http.request(
        "POST",
        f"{HOST}/repos/AlexLanes/python-bot-lib/releases",
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
        f"{HOST}/repos/AlexLanes/python-bot-lib/releases",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {TOKEN}"
        }
    )
    releases = bot.formatos.Json.parse(response.text)
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": { "type": "number" },
                "tag_name": { "type": "string" }
            }
        }
    }
    assert response.status_code == 200 and releases and releases.validar(schema)

    return {
        release["tag_name"]: release["id"]
        for release in releases.valor()
        if release["tag_name"]
    }

def upload_asset (id_release: int, caminho_build: bot.estruturas.Caminho) -> None:
    host = HOST.replace("api", "uploads")
    response = bot.http.request(
        "POST",
        f"{host}/repos/AlexLanes/python-bot-lib/releases/{id_release}/assets",
        params = { "name": caminho_build.nome },
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/octet-stream"
        },
        content = open(caminho_build.string, "rb").read()
    )
    assert response.status_code == 201

def main () -> None:
    """
    - Gerar build na versão especificada no `setup.py`
    - Fazer o upload para o GitHub do release com a tag da versão
    """
    sucesso, _ = bot.sistema.executar("python", "setup.py", "bdist_wheel")
    assert sucesso

    caminho_build, *_ = sorted(
        (c for c in bot.estruturas.Caminho(".", "dist") if c.arquivo()),
        key = lambda c: c.nome,
        reverse = True
    )
    release_atual = "v" + caminho_build.nome.removeprefix("bot-").removesuffix("-py3-none-any.whl")

    releases = obter_releases()
    assert release_atual not in releases, "Versão do release já existente, atualizar versão no setup.py"
    id_release = criar_release(release_atual)
    upload_asset(id_release, caminho_build)

    print(f"\n### Build da versão {release_atual} criado e realizado upload com sucesso para o GitHub ###\n")

if __name__ == "__main__":
    main()
