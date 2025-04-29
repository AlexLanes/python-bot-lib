# std
from __future__ import annotations
import time, enum, typing, collections, weakref, contextlib
from datetime import (
    datetime as Datetime,
    timedelta as Timedelta
)
# interno
from .mensagem import Mensagem
from .. import util, tipagem, logger, sistema, formatos, imagem, estruturas
# externo
import selenium.webdriver as wd
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys as Teclas
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.support.ui import WebDriverWait as Wait, Select
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException as ErroNavegador,
    NoSuchElementException as ElementoNaoEncontrado
)

COMANDO_VERSAO_CHROME = r'(Get-Item -Path "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion'
CONFIG_PRINT_PDF = formatos.Json({
    "version": 2,
    "selectedDestinationId": "Save as PDF",
    "recentDestinations": [{
        "id": "Save as PDF",
        "origin": "local",
        "account": ""
    }]
}).stringify(False)
ARGUMENTOS_DEFAULT = [
    "--ignore-certificate-errors", "--remote-allow-origins=*", "--no-first-run",
    "--no-service-autorun", "--no-default-browser-check", "--homepage=about:blank",
    "--kiosk-printing", "--password-store=basic", "--disable-popup-blocking", "--no-pings",
    "--disable-notifications", "--disable-infobars", "--disable-component-update",
    "--disable-breakpad", "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding",
    "--disable-background-networking", "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process", "--disable-dev-shm-usage",
    "--disable-session-crashed-bubble", "--disable-search-engine-choice-screen"
]

class ElementoWEB:

    __elemento: WebElement
    __localizador: str
    __driver: weakref.ReferenceType[ChromiumDriver]
    __parente: ElementoWEB | None

    def __init__ (self, elemento: WebElement,
                        localizador: str,
                        driver: weakref.ReferenceType[ChromiumDriver],
                        parente: ElementoWEB | None = None) -> None:
        self.__elemento, self.__parente = elemento, parente
        self.__localizador, self.__driver = localizador, driver

    def __repr__ (self) -> str:
        return f"<ElementoWEB {self.elemento}>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, ElementoWEB) and self.elemento == value.elemento

    @property
    def elemento (self) -> WebElement:
        """Elemento original do `selenium`
        - Tentado refazer o elemento caso `StaleElementReferenceException`"""
        elemento = self.__elemento
        try: elemento.is_enabled(); return elemento
        except StaleElementReferenceException: pass

        assert (driver := self.__driver()), "Navegador encerrado"
        find = self.__parente.elemento.find_element if self.__parente else driver.find_element
        estrategia = "xpath" if self.__localizador.startswith(("/", "(", "./")) else "css selector"
        try: self.__elemento = find(estrategia, self.__localizador)
        except ElementoNaoEncontrado:
            raise StaleElementReferenceException("Elemento stale encontrado, tentado recriar sem êxito")

        return self.__elemento

    @property
    def texto (self) -> str:
        """Texto do elemento com `strip()`"""
        return self.elemento.text.strip()

    @property
    def nome (self) -> str:
        """Nome da `<tag>` do elemento"""
        return self.elemento.tag_name

    @property
    def visivel (self) -> bool:
        """Indicador se o elemento está visível"""
        return self.elemento.is_displayed()

    @property
    def ativo (self) -> bool:
        """Indicador se o elemento está habilitado para interação"""
        return self.elemento.is_enabled()

    @property
    def selecionado (self) -> bool:
        """Indicador se o elemento está selecionado
        - Geralmente utilizado em checkbox, opções <select> e botões radio"""
        return self.elemento.is_selected()

    @property
    def select (self) -> Select:
        """Obter a classe de tratamento do elemento `<select>`"""
        return Select(self.elemento)

    @property
    def imagem (self) -> imagem.Imagem:
        """Capturar a imagem do elemento
        - Feito scroll do elemento"""
        assert (driver := self.__driver()), "Navegador encerrado"
        wd.ActionChains(driver).scroll_to_element(self.elemento).perform()
        png = self.sleep(2).elemento.screenshot_as_png
        return imagem.Imagem.from_bytes(png)

    @property
    def atributos (self) -> estruturas.LowerDict[str]:
        """Obter os atributos do elemento"""
        assert (driver := self.__driver()), "Navegador encerrado"
        return estruturas.LowerDict(
            driver.execute_script("""
                let atributos = {}, elemento = arguments[0]
                for (let attr of elemento.attributes) {
                    let valor = elemento[attr.name]
                    atributos[attr.name] = (typeof valor === "string") ? valor : attr.value
                }
                return atributos
            """, self.elemento)
        )

    def sleep (self, segundos: int | float = 0.2) -> typing.Self:
        """Aguardar por `segundos` até continuar a execução"""
        time.sleep(segundos)
        return self

    def hover (self) -> typing.Self:
        """Realizar a ação de hover no elemento"""
        assert (driver := self.__driver()), "Navegador encerrado"
        wd.ActionChains(driver).move_to_element(self.elemento).perform()
        return self.sleep()

    def clicar (self) -> typing.Self:
        """Realizar a ação de click no elemento
        - Aguardado estar clicável"""
        assert (driver := self.__driver()), "Navegador encerrado"

        self.aguardar_clicavel()
        clicado = util.aguardar_condicao(lambda: self.elemento.click() == None, 10, 0.5)
        if not clicado: wd.ActionChains(driver).scroll_to_element(self.elemento)\
                                               .move_to_element(self.elemento)\
                                               .click(self.elemento)\
                                               .perform()

        return self.sleep()

    def limpar (self) -> typing.Self:
        """Limpar o texto do elemento, caso suportado
        - Aguardado estar ativo e atualizar valor"""
        util.aguardar_condicao(lambda: self.ativo, 10, 0.5)

        obter_valor = lambda: self.atributos.get("value", None) or self.texto
        valor = obter_valor()
        self.elemento.clear()

        if valor: util.aguardar_condicao(lambda: valor != obter_valor(), 10, 0.5)
        return self.sleep()

    def digitar (self, *texto: str) -> typing.Self:
        """Digitar o texto no elemento
        - Pode ser combinado com as `Teclas`
        - Hover no elemento, aguardado estar ativo e atualizar valor"""
        try: self.hover()
        except Exception: pass

        util.aguardar_condicao(lambda: self.ativo, 10, 0.5)
        try:
            with self.aguardar_update(5):
                self.elemento.send_keys(*texto)
        except TimeoutError: pass
        return self.sleep()

    def encontrar (self, localizador: str | enum.Enum) -> ElementoWEB:
        """Encontrar o primeiro elemento descendente do `elemento` atual com base no `localizador`
        - Exceção `ElementoNaoEncontrado` caso não seja encontrado
        - Estratégias suportadas:
            - `xpath` se começar com `"/", "(" ou "./"`
            - `css selector` caso contrário"""
        assert self.__driver(), "Navegador encerrado"
        localizador = (localizador if isinstance(localizador, str) else str(localizador.value)).strip()
        estrategia = "xpath" if localizador.startswith(("/", "(", "./")) else "css selector"
        elemento = self.elemento.find_element(estrategia, localizador)
        return ElementoWEB(elemento, localizador, self.__driver, self)

    def procurar (self, localizador: str | enum.Enum) -> list[ElementoWEB]:
        """Procurar elemento(s) descendente(s) do `elemento` atual com base no `localizador`
        - Estratégias suportadas:
            - `xpath` se começar com `"/", "(" ou "./"`
            - `css selector` caso contrário"""
        assert self.__driver(), "Navegador encerrado"
        localizador = (localizador if isinstance(localizador, str) else str(localizador.value)).strip()
        estrategia = "xpath" if localizador.startswith(("/", "(", "./")) else "css selector"
        return [
            ElementoWEB(elemento, localizador, self.__driver, self)
            for elemento in self.elemento.find_elements(estrategia, localizador)
        ]

    def aguardar_clicavel (self, timeout=60) -> typing.Self:
        """Aguardar condição `element_to_be_clickable` do `elemento` por `timeout` segundos
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        assert (driver := self.__driver()), "Navegador encerrado"
        try: Wait(driver, timeout).until(ec.element_to_be_clickable(self.elemento))
        except TimeoutException:
            raise TimeoutError(f"A espera pelo elemento ser clicável não aconteceu após {timeout} segundos")
        except StaleElementReferenceException:
            Wait(driver, timeout).until(ec.element_to_be_clickable(self.elemento))
        return self

    def aguardar_visibilidade (self, timeout=60) -> typing.Self:
        """Aguardar condição `visibility_of` do `elemento` por `timeout` segundos
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        assert (driver := self.__driver()), "Navegador encerrado"
        try: Wait(driver, timeout).until(ec.visibility_of(self.elemento))
        except TimeoutException:
            raise TimeoutError(f"A espera pela visibilidade do elemento não aconteceu após {timeout} segundos")
        except StaleElementReferenceException:
            Wait(driver, timeout).until(ec.visibility_of(self.elemento))
        return self

    @contextlib.contextmanager
    def aguardar_staleness (self, timeout=60) -> typing.Generator[typing.Self, None, None]:
        """Aguardar condição `staleness_of` do `elemento` por `timeout` segundos
        - Exceção `TimeoutError` caso não finalize no tempo estipulado
        - Utilizar com o `with` e realizar uma ação que tornará o elemento stale
            - `with elemento.aguardar_staleness() as elemento: ...`"""
        assert (driver := self.__driver()), "Navegador encerrado"
        try:
            elemento = self.__elemento
            yield self
            Wait(driver, timeout).until(ec.staleness_of(elemento))
        except StaleElementReferenceException: pass
        except TimeoutException:
            raise TimeoutError(f"A espera pelo staleness do elemento não aconteceu após {timeout} segundos")

    @contextlib.contextmanager
    def aguardar_invisibilidade (self, timeout=60) -> typing.Generator[typing.Self, None, None]:
        """Aguardar condição `invisibility_of_element` do `elemento` por `timeout` segundos
        - Checado por staleness do elemento
        - Exceção `TimeoutError` caso não finalize no tempo estipulado
        - Utilizar com o `with` e realizar uma ação que tornará o elemento invisível
            - `with elemento.aguardar_invisibilidade() as elemento: ...`"""
        assert (driver := self.__driver()), "Navegador encerrado"
        try:
            elemento = self.__elemento
            yield self
            Wait(driver, timeout).until(ec.invisibility_of_element(elemento))
        except TimeoutException:
            raise TimeoutError(f"A espera pela invisibilidade do elemento não aconteceu após {timeout} segundos")

    @contextlib.contextmanager
    def aguardar_update (self, timeout=60) -> typing.Generator[typing.Self, None, None]:
        """Aguardar update no `outerHTML` do `elemento` por `timeout` segundos
        - Checado por staleness do elemento
        - Exceção `TimeoutError` caso não finalize no tempo estipulado
        - Utilizar com o `with` e realizar uma ação que alterará o elemento
            - `with elemento.aguardar_update() as elemento: ...`"""
        atributos = self.atributos
        elemento = self.__elemento
        outer = elemento.get_attribute("outerHTML")
        yield self

        def condicao () -> bool:
            try: elemento.is_enabled()
            except StaleElementReferenceException: return True
            return outer != elemento.get_attribute("outerHTML") or atributos != self.atributos

        if not util.aguardar_condicao(condicao, timeout, 0.5):
            raise TimeoutError(f"A espera pelo update do elemento não aconteceu após {timeout} segundos")

class Navegador:
    """Classe do navegador `selenium` que deve ser herdada"""

    driver: ChromiumDriver
    """Driver do `Selenium`"""
    timeout_inicial: float
    """Timeout informado na inicialização do navegador"""
    diretorio_download: sistema.Caminho
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
        """Percorrer as abas, ignorando abas especiais não focáveis, e retornar para a aba original"""
        original = self.aba
        try:
            for aba in self.abas:
                try: self.driver.switch_to.window(aba); yield aba
                except Exception: continue
        finally: self.driver.switch_to.window(original)

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
        """IDs das abas abertas do navegador
        - Usar `for aba in navegador` para focar nas abas e retornar a original ao fim"""
        return self.driver.window_handles

    def sleep (self, segundos: int | float = 5.0) -> typing.Self:
        """Aguardar por `segundos` até continuar a execução"""
        time.sleep(segundos)
        return self

    def titulos (self) -> list[str]:
        """Títulos das abas abertas"""
        return [self.titulo for _ in self]

    def pesquisar (self, url: str) -> typing.Self:
        """Pesquisar o url na aba focada"""
        logger.informar(f"Pesquisando o url '{url}'")
        self.driver.get(url)
        return self

    def atualizar (self) -> typing.Self:
        """Atualizar a aba focada"""
        logger.informar(f"Atualizando aba '{self.titulo}'")
        self.driver.refresh()
        return self.sleep(2)

    def nova_aba (self) -> typing.Self:
        """Abrir uma nova aba e alterar o foco para ela"""
        self.driver.switch_to.new_window("tab")
        logger.informar("Aberto uma nova aba")
        return self

    def fechar_aba (self) -> typing.Self:
        """Fechar a aba focada e alterar o foco para a primeira aba
        - Cria uma nova aba caso só exista uma"""
        aba, titulo = self.aba, self.titulo
        if len([*self]) == 1:
            self.driver.switch_to.new_window("tab")
            self.driver.switch_to.window(aba)
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

    def encontrar (self, localizador: str | enum.Enum) -> ElementoWEB:
        """Encontrar o primeiro elemento na aba atual com base no `localizador`
        - Exceção `ElementoNaoEncontrado` caso não seja encontrado
        - Estratégias suportadas:
            - `xpath` se começar com `"/", "(" ou "./"`
            - `css selector` caso contrário"""
        localizador = (localizador if isinstance(localizador, str) else str(localizador.value)).strip()
        estrategia = "xpath" if localizador.startswith(("/", "(", "./")) else "css selector"
        elemento = self.driver.find_element(estrategia, localizador)
        return ElementoWEB(elemento, localizador, weakref.ref(self.driver))

    def procurar (self, localizador: str | enum.Enum) -> list[ElementoWEB]:
        """Procurar elemento(s) na aba atual com base no `localizador`
        - Estratégias suportadas:
            - `xpath` se começar com `"/", "(" ou "./"`
            - `css selector` caso contrário"""
        localizador = (localizador if isinstance(localizador, str) else str(localizador.value)).strip()
        estrategia = "xpath" if localizador.startswith(("/", "(", "./")) else "css selector"
        ref = weakref.ref(self.driver)
        return [
            ElementoWEB(elemento, localizador, ref)
            for elemento in self.driver.find_elements(estrategia, localizador)
        ]

    def alterar_frame (self, frame: str | ElementoWEB | None = None) -> typing.Self:
        """Alterar o frame atual do DOM da página para o `frame` contendo `@name, @id ou ElementoWEB`
        - Necessário para encontrar e interagir com elementos dentro de `<iframes>`
        - `None` para retornar ao default_content (raiz)"""
        s = self.driver.switch_to
        if frame == None: s.default_content()
        else: s.frame(frame if isinstance(frame, str) else frame.elemento)
        return self

    def alterar_timeout (self, timeout: float | None = None) -> typing.Self:
        """Alterar o tempo de `timeout` para ações realizadas pelo navegador
        - `None` para retornar ao timeout de inicialização"""
        timeout = timeout if timeout != None else self.timeout_inicial
        self.driver.implicitly_wait(timeout)
        return self

    def aguardar_titulo (self, titulo: str, timeout=30) -> typing.Self:
        """Aguardar alguma aba conter o `título` e alterar o foco para ela
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        aba_com_titulo: str | None = None
        titulo_normalizado = util.normalizar(titulo)

        def aba_contendo_titulo () -> bool:
            nonlocal aba_com_titulo
            for aba in self:
                if titulo_normalizado in util.normalizar(self.titulo):
                    aba_com_titulo = aba
                    return True
            return False

        if not util.aguardar_condicao(aba_contendo_titulo, timeout, 1):
            raise TimeoutError(f"Aba contendo o título '{titulo}' não foi encontrada após {timeout} segundos")

        return self.focar_aba(aba_com_titulo)

    def aguardar_download (self, *termos: str, timeout=60) -> sistema.Caminho:
        """Aguardar um novo arquivo, com nome contendo algum dos `termos`, no diretório de download por `timeout` segundos
        - Retorna o `Caminho` para o arquivo
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        inicio = Datetime.now() - Timedelta(milliseconds=500)
        arquivo: sistema.Caminho | None = None
        termos = tuple(str(termo).lower() for termo in termos)
        assert termos, "Pelo menos 1 termo é necessário para a busca"

        def download_finalizar () -> bool:
            nonlocal arquivo
            arquivo, *_ = [
                caminho
                for caminho in self.diretorio_download
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
        assert arquivo
        return arquivo

    def imprimir_pdf (self) -> sistema.Caminho:
        """Imprimir a página/frame atual do navegador para `.pdf`
        - Retorna o `Caminho` para o arquivo"""
        self.diretorio_download.criar_diretorios()
        self.driver.execute_script("window.print();")
        return self.aguardar_download(".pdf", timeout=20)

class Edge (Navegador):
    """Navegador Edge baseado no `selenium`
    - `timeout` utilizado na espera por elementos
    - `download` diretório para download de arquivos
    - O Edge é o mais provável de estar disponível para utilização"""

    def __init__ (self, timeout=30.0,
                        download: str | sistema.Caminho = "./downloads") -> None:
        options, argumentos = wd.EdgeOptions(), ARGUMENTOS_DEFAULT.copy()
        self.diretorio_download = sistema.Caminho(download) if isinstance(download, str) else download
        for argumento in argumentos: options.add_argument(argumento)
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 2,

            "download.directory_upgrade": True,
            "download.prompt_for_download": False,
            "download.default_directory": self.diretorio_download.string,

            "savefile.default_directory": self.diretorio_download.string,
            "printing.print_preview_sticky_settings.appState": CONFIG_PRINT_PDF
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
    - `download` diretório para download de arquivos
    - `extensoes` caminhos para extensões existentes do Chrome
    - `perfil` caminho para o perfil que será utilizado na abertura do navegador
    - Utilizada a biblioteca `undetected_chromedriver` para evitar detecção (Modo anônimo ocasiona a detecção)
    - Possível de capturar as mensagens de rede pelo método `mensagens_rede`"""

    def __init__ (self, timeout=30.0,
                        download: str | sistema.Caminho = "./downloads",
                        extensoes: list[str | sistema.Caminho] = [],
                        perfil: sistema.Caminho | str | None = None,
                        argumentos_adicionais: list[str] = []) -> None:
        # obter a versão do google chrome para o `undetected_chromedriver`, pois ele utiliza sempre a mais recente
        sucesso, mensagem = sistema.executar(COMANDO_VERSAO_CHROME, powershell=True)
        versao = (mensagem.split(".") or " ")[0]
        if not sucesso or not versao.isdigit():
            raise Exception("Versão do Google Chrome não foi localizada")

        argumentos = { *ARGUMENTOS_DEFAULT, *argumentos_adicionais }
        if extensoes: argumentos.add(f"--load-extension={ ",".join(str(e).strip() for e in extensoes) }")
        if perfil:
            perfil = sistema.Caminho(str(perfil))
            argumentos.add(f"--user-data-dir={perfil.parente}")
            argumentos.add(f"--profile-directory={perfil.nome}")

        options = uc.ChromeOptions()
        self.diretorio_download = sistema.Caminho(str(download))
        for argumento in argumentos:
            options.add_argument(argumento)
        options.set_capability("goog:loggingPrefs", { "performance": "ALL" }) # logs performance
        options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_settings.popups": 2,

            "download.directory_upgrade": True,
            "download.prompt_for_download": False,
            "download.default_directory": self.diretorio_download.string,

            "savefile.default_directory": self.diretorio_download.string,
            "printing.print_preview_sticky_settings.appState": CONFIG_PRINT_PDF
        })

        self.driver = uc.Chrome(options, version_main=int(versao)) # type: ignore
        self.driver.maximize_window()
        self.timeout_inicial = timeout
        self.driver.implicitly_wait(timeout)

        logger.informar("Navegador Chrome iniciado")

    def __repr__ (self) -> str:
        return f"<Chrome aba focada '{self.titulo}'>"

    @typing.override
    def __del__ (self) -> None:
        logger.informar("Navegador fechado")
        try: getattr(self.driver, "quit", lambda: "")()
        # usado TASKKILL ao fim da execução caso tenha ocorrido erro
        except: sistema.executar("TASKKILL", "/F", "/IM", "chrome.exe", timeout=5)

    def mensagens_rede (self, filtro: typing.Callable[[Mensagem], bool] | None = None) -> list[Mensagem]:
        """Consultar as mensagens de rede produzidas pelas abas
        - `filtro` função opcional para filtrar as mensagens"""
        id_mensagem = collections.defaultdict(Mensagem)
        for log in self.driver.get_log("performance"):
            if not isinstance(log, dict): continue
            json, _ = formatos.Json.parse(log.get("message", {}))
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

    def __init__ (self, timeout=30.0) -> None:
        options = wd.IeOptions()
        options.attach_to_edge_chrome = True
        options.add_argument("--ignore-certificate-errors")

        self.driver = wd.Ie(options) # type: ignore
        self.driver.maximize_window()
        self.timeout_inicial = timeout
        self.driver.implicitly_wait(timeout)

        logger.informar("Navegador Edge, modo Internet Explorer, iniciado")

    def __repr__ (self) -> str:
        return f"<Explorer aba focada '{self.titulo}'>"

    @typing.override
    def aguardar_download (self, *termos: str, timeout=60) -> sistema.Caminho:
        raise NotImplementedError("Método aguardar_download não disponível para o InternetExplorer")

__all__ = [
    "Edge",
    "Teclas",
    "Chrome",
    "Explorer",
    "ErroNavegador",
    "ElementoNaoEncontrado"
]