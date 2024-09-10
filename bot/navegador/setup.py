# std
import time, enum, typing, atexit, collections
from datetime import (
    datetime as Datetime,
    timedelta as Timedelta
)
# interno
from .mensagem import Mensagem
from .. import util, tipagem, logger, sistema, formatos, estruturas
# externo
import selenium.webdriver as wd
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys as Teclas
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException as ErroNavegador,
    NoSuchElementException as ElementoNaoEncontrado
)

SCRIPT_NOVA_GUIA = "window.open('').focus()"
COMANDO_VERSAO_CHROME = r'(Get-Item -Path "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion'

class Navegador:
    """Classe do navegador `selenium` que deve ser herdada"""

    driver: wd.Edge
    """Driver do `Selenium`"""
    timeout_inicial: float
    """Timeout informado na inicialização do navegador"""
    diretorio_dowload: estruturas.Caminho
    """Caminho da pasta de download
    - `Edge | Chrome`"""

    def __del__ (self) -> None:
        """Encerrar o driver quando a variável do navegador sair do escopo"""
        try:
            self.driver.quit()
            logger.informar("Navegador fechado")
            del self.driver
        except: pass

    def __setattr__ (self, nome: str, valor: typing.Any) -> None:
        if getattr(self, nome, None) != None:
            raise AttributeError("Não é possível alterar atributos/métodos")
        object.__setattr__(self, nome, valor)

    def __iter__ (self) -> typing.Generator[str, None, None]:
        """Percorrer as abas, ignorando as especiais, e retornar à original
        - Caso tenha sido feito `break/return` no iterator, o retorno à aba original não acontece"""
        original = self.aba
        especial = lambda: self.url.lower().strip().startswith(("edge", "chrome"))
        for aba in self.abas:
            try:
                self.driver.switch_to.window(aba)
                if not especial(): yield aba
            except Exception: pass
        self.driver.switch_to.window(original)

    @property
    def titulo (self) -> str:
        """Título da aba focada"""
        return self.driver.title

    @property
    def url (self) -> tipagem.url:
        """Url atual da aba focada"""
        return self.driver.current_url

    @property
    def aba (self) -> str:
        """ID da aba do navegador focada"""
        return self.driver.current_window_handle

    @property
    def abas (self) -> list[str]:
        """IDs das abas abertas do navegador"""
        return self.driver.window_handles

    def titulos (self) -> list[str]:
        """Títulos das abas abertas"""
        return [self.titulo for _ in self]

    def pesquisar (self, url: str) -> typing.Self:
        """Pesquisar o url na aba focada"""
        logger.informar(f"Pesquisado o url '{url}'")
        self.driver.get(url)
        return self

    def nova_aba (self) -> typing.Self:
        """Abrir uma nova aba e alterar o foco para ela"""
        # driver.switch_to.new_window("tab") não funciona em modo anônimo
        abas = set(self.abas)
        self.driver.execute_script(SCRIPT_NOVA_GUIA)
        novo_handle, *_ = set(self.abas).difference(abas)
        self.driver.switch_to.window(novo_handle)
        logger.informar("Aberto uma nova aba")
        return self

    def fechar_aba (self) -> typing.Self:
        """Fechar a aba focada e alterar o foco para a primeira aba
        - Cria uma nova aba caso só exista uma"""
        titulo = self.titulo
        if len(self.abas) == 1:
            self.driver.execute_script(SCRIPT_NOVA_GUIA)
        self.driver.close()
        self.driver.switch_to.window(self.abas[0])
        logger.informar(f"Fechado a aba '{titulo}' e focado na aba '{self.titulo}'")
        return self

    def limpar_abas (self) -> typing.Self:
        """Fechar as abas abertas, abrir uma nova e focar"""
        logger.informar("Limpando as abas abertas do navegador")
        nova_aba = self.nova_aba().aba
        for aba in self:
            if aba == nova_aba: continue
            try: self.driver.close()
            except Exception: pass
        return self

    def focar_aba (self, identificador: str | None = None) -> typing.Self:
        """Focar na aba com base no `identificador`
        - `None` para focar na primeira aba"""
        self.driver.switch_to.window(identificador or self.abas[0])
        logger.informar(f"O navegador focou na aba '{self.titulo}'")
        return self

    def encontrar_elemento (self, estrategia: tipagem.ESTRATEGIAS_WEBELEMENT, localizador: str | enum.Enum) -> WebElement:
        """Encontrar elemento na aba atual com base em um `localizador` para a `estrategia` selecionada
        - Exceção `ElementoNaoEncontrado` caso não seja encontrado"""
        localizador: str = localizador if isinstance(localizador, str) else str(localizador.value)
        logger.debug(f"Procurando elemento no navegador ('{estrategia}', '{localizador}')")
        return self.driver.find_element(estrategia, localizador)

    def encontrar_elementos (self, estrategia: tipagem.ESTRATEGIAS_WEBELEMENT, localizador: str | enum.Enum) -> list[WebElement]:
        """Encontrar elemento(s) na aba atual com base em um `localizador` para a `estrategia` selecionada"""
        localizador = localizador if isinstance(localizador, str) else str(localizador.value)
        logger.debug(f"Procurando elementos no navegador ('{estrategia}', '{localizador}')")
        elementos = self.driver.find_elements(estrategia, localizador)
        return elementos

    def alterar_frame (self, frame: str | WebElement | None = None) -> typing.Self:
        """Alterar o frame atual do DOM da página para o `frame` contendo `@name, @id ou WebElement`
        - Necessário para encontrar e interagir com `WebElements` dentro de `<iframes>`
        - `None` para retornar ao default_content (raiz)"""
        logger.debug(f"Alterando frame da aba '{self.titulo}'")
        s = self.driver.switch_to
        s.frame(frame) if frame else s.default_content()
        return self

    def alterar_timeout (self, timeout: float | None = None) -> typing.Self:
        """Alterar o tempo de `timeout` para ações realizadas pelo navegador
        - `None` para retornar ao timeout de inicialização"""
        timeout = timeout if timeout != None else self.timeout_inicial
        self.driver.implicitly_wait(timeout)
        return self

    def hover_elemento (self, elemento: WebElement) -> typing.Self:
        """Realizar a ação de hover no `elemento`"""
        logger.debug(f"Realizando ação de hover no elemento '{elemento}'")
        wd.ActionChains(self.driver).move_to_element(elemento).perform()
        return self

    def aguardar_titulo (self, titulo: str, timeout=30) -> typing.Self:
        """Aguardar alguma aba conter o `título` e alterar o foco para ela
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        normalizado = util.normalizar(titulo)
        def alguma_aba_contem_titulo () -> bool:
            for _ in self:
                if normalizado in util.normalizar(self.titulo):
                    return True
            return False

        if not util.aguardar_condicao(alguma_aba_contem_titulo, timeout, 1):
            raise TimeoutError(f"Aba contendo o título '{titulo}' não foi encontrada após {timeout} segundos")
        return self

    def aguardar_staleness (self, elemento: WebElement, timeout=60) -> typing.Self:
        """Aguardar a condição staleness_of do `elemento` por `timeout` segundos
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        try:
            Wait(self.driver, timeout).until(ec.staleness_of(elemento))
            return self
        except TimeoutException:
            raise TimeoutError(f"A espera pelo staleness do Elemento não aconteceu após {timeout} segundos")

    def aguardar_visibilidade (self, elemento: WebElement, timeout=60) -> typing.Self:
        """Aguardar a condição visibility_of do `elemento` por `timeout` segundos
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        try:
            Wait(self.driver, timeout).until(ec.visibility_of(elemento))
            return self
        except TimeoutException:
            raise TimeoutError(f"A espera pela visibilidade do Elemento não aconteceu após {timeout} segundos")

    def aguardar_download (self, *termos: str, timeout=60) -> estruturas.Caminho:
        """Aguardar um novo arquivo, com nome contendo algum dos `termos`, no diretório de download por `timeout` segundos
        - Retorna o `Caminho` para o arquivo
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        inicio = Datetime.now() - Timedelta(milliseconds=500)
        arquivo: estruturas.Caminho | None = None
        termos = [str(termo).lower() for termo in termos]
        assert termos, "Pelo menos 1 termo é necessário para a busca"

        def download_finalizar () -> bool:
            nonlocal arquivo
            arquivo, *_ = [
                caminho
                for caminho in self.diretorio_dowload
                if all((
                    caminho.arquivo(),
                    not caminho.nome.lower().endswith(".crdownload"),
                    any(termo in caminho.nome.lower() for termo in termos),
                    any(data >= inicio for data in (caminho.data_criacao, caminho.data_modificao))
                ))
            ] or [None]
            return arquivo != None

        if not util.aguardar_condicao(download_finalizar, timeout):
            erro = TimeoutError(f"Espera por download não encontrou nenhum arquivo novo após {timeout} segundos")
            erro.add_note(f"Termos esperados: {termos}")
            raise erro

        time.sleep(1)
        return arquivo

    def coordenada_elemento (self, elemento: WebElement) -> estruturas.Coordenada:
        """Obter a coordenada do `elemento` referente a tela
        - Scroll do `elemento` para o centro da tela
        - Não funciona para elementos dentro de iframe"""
        coordenada = self.driver.execute_script(
            """
            arguments[0].scrollIntoView({ block: "center" });
            const y_offset = window.outerHeight - window.innerHeight,
                  rect = arguments[0].getBoundingClientRect();
            return {
                x: Math.ceil(rect.x),
                y: Math.ceil(rect.y + y_offset),
                largura: Math.floor(rect.width),
                altura: Math.floor(rect.height)
            };
            """,
            elemento
        )
        return estruturas.Coordenada(**coordenada)

    def imprimir_pdf (self) -> estruturas.Caminho:
        """Imprimir a página/frame atual do navegador para `.pdf`
        - Retorna o `Caminho` para o arquivo"""
        self.driver.execute_script("window.print();")
        return self.aguardar_download(".pdf", timeout=20)

class Edge (Navegador):
    """Navegador Edge baseado no `selenium`
    - `timeout` utilizado na espera por elementos
    - `download` diretório para download/impressão de arquivos
    - `anonimo` para abrir o navegador como inprivate"
    - O Edge é o mais provável de estar disponível para utilização"""

    driver: wd.Edge
    """Driver Edge"""

    def __init__ (self, timeout=30.0,
                        download: str | estruturas.Caminho = "./downloads",
                        anonimo=False) -> None:
        options = wd.EdgeOptions()
        self.diretorio_dowload = estruturas.Caminho(download) if isinstance(download, str) else download
        argumentos = [
            "--ignore-certificate-errors", "--disable-infobars", "--disable-notifications",
            "--start-maximized", "--kiosk-printing", "--disable-blink-features=AutomationControlled"
        ]
        if anonimo: argumentos.append("--inprivate")

        for argumento in argumentos: options.add_argument(argumento)
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        options.add_experimental_option("prefs", {
            "download.directory_upgrade": True,
            "download.prompt_for_download": False,
            "savefile.default_directory": self.diretorio_dowload.string,
            "download.default_directory": self.diretorio_dowload.string,
            "printing.print_preview_sticky_settings.appState": formatos.Json({
                "recentDestinations": [{ "id": "Save as PDF", "origin": "local", "account": "" }],
                "selectedDestinationId": "Save as PDF", "version": 2
            }).stringify(False)
        })

        self.driver = wd.Edge(options)
        self.driver.maximize_window()
        self.timeout_inicial = timeout
        self.driver.implicitly_wait(timeout)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, "webdriver", {
                    get: () => false
                })
            """
        })

        logger.informar("Navegador Edge iniciado")

    def __repr__ (self) -> str:
        return f"<Edge aba focada '{self.titulo}'>"

class Chrome (Navegador):
    """Navegador Chrome baseado no `selenium`
    - `timeout` utilizado na espera por elementos
    - `download` diretório para download/impressão de arquivos
    - Utilizada a biblioteca `undetected_chromedriver` para evitar detecção (Modo anônimo ocasiona a detecção)
    - Possível de capturar as mensagens de rede pelo método `mensagens_rede`"""

    driver: uc.Chrome
    """Driver Chrome"""

    def __init__ (self, timeout=30.0,
                        download: str | estruturas.Caminho = "./downloads") -> None:
        # obter a versão do google chrome para o `undetected_chromedriver`, pois ele utiliza sempre a mais recente
        sucesso, mensagem = sistema.executar(COMANDO_VERSAO_CHROME, powershell=True)
        versao = (mensagem.split(".") or " ")[0]
        if not sucesso or not versao.isdigit():
            raise Exception("Versão do Google Chrome não foi localizada")

        options = uc.ChromeOptions()
        self.diretorio_dowload = estruturas.Caminho(download) if isinstance(download, str) else download
        argumentos = [
            "--start-maximized", "--disable-infobars", "--disable-notifications",
            "--ignore-certificate-errors", "--kiosk-printing", "--disable-popup-blocking"
        ]

        for argumento in argumentos: options.add_argument(argumento)
        options.set_capability("goog:loggingPrefs", { "performance": "ALL" }) # logs performance
        options.add_experimental_option("prefs", {
            "download.directory_upgrade": True,
            "download.prompt_for_download": False,
            "download.default_directory": self.diretorio_dowload.string,
            "savefile.default_directory": self.diretorio_dowload.string,
            "printing.print_preview_sticky_settings.appState": formatos.Json({
                "recentDestinations": [{ "id": "Save as PDF", "origin": "local", "account": "" }],
                "selectedDestinationId": "Save as PDF", "version": 2
            }).stringify(False)
        })

        self.driver = uc.Chrome(options, version_main=int(versao))
        self.driver.maximize_window()
        self.timeout_inicial = timeout
        self.driver.implicitly_wait(timeout)

        logger.informar("Navegador Chrome iniciado")

        # `undetected_chromedriver` está com problema intermitente ao fechar
        # a task que é aberta ao criar o driver está ficando ativa após o `quit()`
        atexit.register(lambda: sistema.executar("TASKKILL", "/F", "/IM", "chrome.exe", timeout=5))

    def __repr__ (self) -> str:
        return f"<Chrome aba focada '{self.titulo}'>"

    @typing.override
    def __del__ (self) -> None:
        logger.informar("Navegador fechado")
        try: self.driver.quit()
        except OSError: pass # usado TASKKILL ao fim da execução

    def mensagens_rede (self, filtro: typing.Callable[[Mensagem], bool] | None = None) -> list[Mensagem]:
        """Consultar as mensagens de rede produzidas pelas abas
        - `filtro` função opcional para filtrar as mensagens"""
        id_mensagem = collections.defaultdict(Mensagem)
        for log in self.driver.get_log("performance"):
            if not isinstance(log, dict): continue
            json = formatos.Json.parse(log.get("message", {}))
            if not json or not json.message.params.requestId: continue

            message = json.message
            params = message.params
            request_id = params.requestId.valor()
            mensagem = id_mensagem[request_id]

            if "Network.request" in message.method:
                mensagem.parse_request(params)
            elif "Network.response" in message.method:
                mensagem.parse_response(params)
                try:
                    body = mensagem.response.body or self.driver.execute_cdp_cmd("Network.getResponseBody", { "requestId": request_id })
                    mensagem.response.body = body
                except Exception: pass

        filtro = filtro or (lambda m: True)
        return list(
            mensagem
            for mensagem in id_mensagem.values()
            if filtro(mensagem)
        )

class Explorer (Navegador):
    r"""Navegador Edge no modo Internet Explorer
    - `timeout` utilizado na espera por elementos
    - Selenium avisa sobre a necesidade do driver no %PATH%, mas consegui utilizar sem o driver
    - Necessário desativar o Protected Mode em `Internet Options -> Security` para todas as zonas
    - Caso não apareça a opção, alterar pelo registro do windows `Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones` em todas as zonas(0..4) setando o `REG_DWORD` nome `2500` valor `3`
    - https://www.lifewire.com/how-to-disable-protected-mode-in-internet-explorer-2624507"""

    driver: wd.Ie
    """Driver Internet Explorer"""

    def __init__ (self, timeout=30.0) -> None:
        options = wd.IeOptions()
        options.attach_to_edge_chrome = True
        options.add_argument("--ignore-certificate-errors")

        self.driver = wd.Ie(options)
        self.driver.maximize_window()
        self.timeout_inicial = timeout
        self.driver.implicitly_wait(timeout)

        logger.informar("Navegador Edge, modo Internet Explorer, iniciado")

    def __repr__ (self) -> str:
        return f"<Explorer aba focada '{self.titulo}'>"

    @typing.override
    def aguardar_download (self, termos: list[str] = [".csv", "arquivo.xlsx"], timeout=60) -> str:
        raise NotImplementedError("Método aguardar_download não disponível para o InternetExplorer")

__all__ = [
    "Edge",
    "Teclas",
    "Chrome",
    "Explorer",
    "ErroNavegador",
    "ElementoNaoEncontrado"
]
