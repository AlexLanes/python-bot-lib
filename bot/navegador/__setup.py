# std
from abc import ABC
from enum import Enum
from typing import Self
from datetime import (
    datetime as Datetime,
    timedelta as TimeDelta
)
# interno
from .. import util, tipagem, logger, windows, teclado
# externo
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys as Teclas
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Ie as WebDriverIe, IeOptions
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver import Edge as WebDriverEdge, EdgeOptions
from selenium.webdriver import Chrome as WebDriverChrome, ChromeOptions
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException as ElementoNaoEncontrado
)

class Navegador (ABC):
    """Classe do navegador abstrata que deve ser herdada"""

    driver: WebDriverEdge | WebDriverChrome | WebDriverIe
    """Driver do `Selenium`"""
    diretorio_dowload: tipagem.caminho
    """Caminho da pasta de download
    - `Edge` | `Chrome`
    - Não é possível alterar"""

    def __del__ (self) -> None:
        """Encerrar o driver quando a variável do navegador sair do escopo"""
        try: self.driver.quit()
        except: pass
        logger.informar("Navegador fechado")

    @property
    def titulo (self) -> str:
        """Título da aba focada"""
        return self.driver.title

    @property
    def url (self) -> tipagem.url:
        """Url atual da aba focada"""
        return self.driver.current_url

    @property
    def abas (self) -> list[str]:
        """ID das abas/janelas abertas do driver atual do navegador"""
        return self.driver.window_handles

    def titulos (self) -> list[str]:
        """Títulos das abas abertas"""
        original, titulos = self.driver.current_window_handle, [
            self.titulo
            for aba in self.abas
            if not self.driver.switch_to.window(aba)
        ]
        self.driver.switch_to.window(original)
        return titulos

    def pesquisar (self, url: str) -> Self:
        """Pesquisar o url na aba focada"""
        logger.informar(f"Pesquisado o url '{url}'")
        self.driver.get(url)
        return self

    def nova_aba (self) -> Self:
        """Abrir uma nova aba e alterar o foco para ela"""
        self.driver.switch_to.new_window("tab")
        logger.informar("Aberto uma nova aba")
        return self

    def fechar_aba (self) -> Self:
        """Fechar a aba focada e alterar o foco para a anterior"""
        titulo = self.driver.title
        self.driver.close()
        self.driver.switch_to.window(self.abas[-1])
        logger.informar(f"Fechado a aba '{titulo}' e focado na aba '{self.titulo}'")
        return self

    def limpar_abas (self) -> Self:
        """Fechar as abas abertas, abrir uma nova e focar"""
        logger.informar("Limpando as abas abertas do navegador")
        self.driver.switch_to.new_window("tab")
        nova_aba = self.driver.current_window_handle

        for aba in self.abas:
            if aba == nova_aba: continue
            self.driver.switch_to.window(aba)
            if self.driver.title.strip().lower() == "downloads":
                teclado.apertar_tecla("esc", delay=0.5)
                continue
            self.driver.close()

        self.driver.switch_to.window(nova_aba)
        return self

    def focar_aba (self, titulo: str | None = None) -> Self:
        """Focar na aba que contem o `titulo`
        - `None` para focar na última aba"""
        titulo = util.normalizar(titulo) if titulo else None
        if not titulo:
            self.driver.switch_to.window(self.abas[-1])
            logger.informar(f"O navegador focou na aba '{self.driver.title}'")
            return self

        for aba in self.abas:
            self.driver.switch_to.window(aba)
            if titulo not in util.normalizar(self.driver.title): continue
            logger.informar(f"O navegador focou na aba '{self.driver.title}'")
            break

        return self

    def encontrar_elemento (self, estrategia: tipagem.ESTRATEGIAS_WEBELEMENT, localizador: str | Enum) -> WebElement:
        """Encontrar elemento na aba atual com base em um `localizador` para a `estrategia` selecionada
        - Exceção `ElementoNaoEncontrado` caso não seja encontrado"""
        localizador: str = localizador if isinstance(localizador, str) else str(localizador.value)
        logger.debug(f"Procurando elemento no navegador ('{estrategia}', '{localizador}')")
        return self.driver.find_element(estrategia, localizador)

    def encontrar_elementos (self, estrategia: tipagem.ESTRATEGIAS_WEBELEMENT, localizador: str | Enum) -> list[WebElement]:
        """Encontrar elemento(s) na aba atual com base em um `localizador` para a `estrategia` selecionada"""
        localizador = localizador if isinstance(localizador, str) else str(localizador.value)
        logger.debug(f"Procurando elementos no navegador ('{estrategia}', '{localizador}')")
        elementos = self.driver.find_elements(estrategia, localizador)
        return elementos

    def alterar_frame (self, frame: str | WebElement | None = None) -> Self:
        """Alterar o frame atual do DOM da página para o `frame` contendo `@name, @id ou WebElement`
        - Necessário para encontrar e interagir com `WebElements` dentro de `<iframes>`
        - `None` para retornar ao default_content (raiz)"""
        logger.debug(f"Alterando frame da aba '{self.titulo}'")
        s = self.driver.switch_to
        s.frame(frame) if frame else s.default_content()
        return self

    def hover_elemento (self, elemento: WebElement) -> Self:
        """Realizar a ação de hover no `elemento`"""
        logger.debug(f"Realizando ação de hover no elemento '{elemento}'")
        ActionChains(self.driver).move_to_element(elemento).perform()
        return self

    def aguardar_staleness (self, elemento: WebElement, timeout=60) -> Self:
        """Aguardar a condição staleness_of do `elemento` por `timeout` segundos
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        try:
            Wait(self.driver, timeout).until(staleness_of(elemento))
            return self
        except TimeoutException:
            raise TimeoutError(f"A espera pelo staleness do Elemento não aconteceu após {timeout} segundos")

    def aguardar_download (self, termos: list[str] = [".csv", "arquivo.xlsx"],
                                 timeout = 60) -> tipagem.caminho:
        """Aguardar um novo arquivo, que termine com algum dos `termos`, no diretório de download por `timeout` segundos
        - Retorna o caminho para o arquivo
        - Exceção `TimeoutError` caso não finalize no tempo estipulado"""
        assert termos, "Pelo menos 1 termo é necessário para a busca do arquivo"
        caminho_arquivo: tipagem.caminho | None = None
        inicio = Datetime.now() - TimeDelta(seconds=1)

        def download_finalizado () -> bool:
            nonlocal inicio, caminho_arquivo
            for caminho, _ in windows.listar_diretorio(self.diretorio_dowload) \
                                     .query_data_alteracao_arquivos(inicio, Datetime.now()):
                if not any(caminho.endswith(termo) for termo in termos): continue
                caminho_arquivo = caminho
                return True
            return False

        if not util.aguardar_condicao(download_finalizado, timeout, 0.5):
            erro = TimeoutError(f"Espera por download não encontrou nenhum arquivo novo após {timeout} segundos")
            erro.add_note(f"Termos esperados: {termos}")
            raise erro
        return caminho_arquivo

class Edge (Navegador):
    """Navegador Edge"""

    driver: WebDriverEdge
    """Driver Edge"""

    def __init__ (self, timeout=30.0, download=rf"./downloads") -> None:
        """Inicializar o navegador Edge
        - `timeout` utilizado na espera do `implicitly_wait`
        - `download` utilizado para informar a pasta de download de arquivos"""
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option("excludeSwitches", ["enable-logging"]) # desativar prints

        self.diretorio_dowload = windows.caminho_absoluto(download)
        options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.default_directory": self.diretorio_dowload,
        })

        self.driver = WebDriverEdge(options)
        self.driver.implicitly_wait(timeout)
        self.driver.maximize_window()

        logger.informar("Navegador Edge iniciado")

class Chrome (Navegador):
    """Navegador Chrome"""

    driver: WebDriverChrome
    """Driver Chrome"""

    def __init__ (self, timeout=30.0, download=rf"./downloads") -> None:
        """Inicializar o navegador Chrome
        - `timeout` utilizado na espera do `implicitly_wait`
        - `download` utilizado para informar a pasta de download de arquivos"""
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option("excludeSwitches", ["enable-logging"]) # desativar prints

        self.diretorio_dowload = windows.caminho_absoluto(download)
        options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.default_directory": self.diretorio_dowload,
        })

        self.driver = WebDriverChrome(options)
        self.driver.implicitly_wait(timeout)
        self.driver.maximize_window()

        logger.informar("Navegador Chrome iniciado")

class Explorer (Navegador):
    r"""Navegador Internet Explorer
    - Selenium avisa sobre a necesidade do driver no %PATH%, mas consegui utilizar sem o driver
    - Necessário desativar o Protected Mode em `Internet Options -> Security` para todas as zonas
    - Caso não apareça a opção, alterar pelo registro do windows `Software\Microsoft\Windows\CurrentVersion\Internet Settings\Zones` em todas as zonas(0..4) setando o `REG_DWORD` nome `2500` valor `3`
    - https://www.lifewire.com/how-to-disable-protected-mode-in-internet-explorer-2624507"""

    driver: WebDriverIe
    """Driver Internet Explorer"""

    def __init__ (self, timeout=30.0) -> None:
        """Inicializar o navegador Edge no modo Internet Explorer
        - `timeout` utilizado na espera do `implicitly_wait`"""
        options = IeOptions()
        options.attach_to_edge_chrome = True
        options.add_argument("--ignore-certificate-errors")

        self.driver = WebDriverIe(options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(timeout)

        logger.informar("Navegador Edge, modo Internet Explorer, iniciado")

__all__ = [
    "Edge",
    "Teclas",
    "Chrome",
    "Explorer",
    "ElementoNaoEncontrado"
]
