# std
from abc import ABC
from enum import Enum
# interno
import bot
# externo
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Ie as WebDriverIe, IeOptions
from selenium.webdriver import Edge as WebDriverEdge, EdgeOptions
from selenium.webdriver import Chrome as WebDriverChrome, ChromeOptions


class Navegador (ABC):
    """Classe do navegador abstrata que deve ser herdada"""

    driver: WebDriverEdge | WebDriverChrome | WebDriverIe
    """Driver do `Selenium`"""
    
    def __del__ (self):
        """Encerrar o driver quando a variável do navegador sair do escopo"""
        self.driver.quit()
        bot.logger.informar("Navegador fechado")

    @property
    def abas (self) -> list[str]:
        """ID das abas/janelas abertas do driver atual do navegador"""
        return self.driver.window_handles

    def pesquisar (self, url: str):
        """Pesquisar o url na aba focada"""
        bot.logger.informar(f"Pesquisado o url '{ url }'")
        self.driver.get(url)
        return self

    def nova_aba (self):
        """Abrir uma nova aba e alterar o foco para ela"""
        self.driver.switch_to.new_window("tab")
        bot.logger.informar("Aberto uma nova aba")
        return self

    def fechar_aba (self):
        """Fechar a aba focada e alterar o foco para a anterior"""
        titulo = self.driver.title
        self.driver.close()
        self.driver.switch_to.window(self.abas[-1])
        bot.logger.informar(f"Fechado a aba '{ titulo }'")
        return self
    
    def focar_aba (self, titulo: str = None) -> None:
        """Focar na aba que contem o `titulo`
        - `titulo` None para focar na primera aba diferente da atual"""
        original = self.driver.current_window_handle
        for aba in self.abas:
            self.driver.switch_to.window(aba)
            if (titulo == None and aba != original) or (titulo != None and bot.util.normalizar(titulo) in bot.util.normalizar(self.driver.title)):
                return bot.logger.informar(f"O navegador focou na aba '{ self.driver.title }'")
            self.driver.switch_to.window(original)

        bot.logger.alertar(f"Nenhuma aba encontrada que possua o título '{ titulo }' foi encontrada")

    def encontrar_elemento (self, estrategia: bot.tipagem.ESTRATEGIAS_WEBELEMENT, localizador: str | Enum) -> WebElement | None:
        """Encontrar elemento(s) na aba atual com base em um `localizador` para a `estrategia` selecionada"""
        localizador: str = localizador if isinstance(localizador, str) else str(localizador.value)
        bot.logger.debug(f"Procurando elemento no navegador ('{ estrategia }', '{ localizador }')")
        elemento = self.driver.find_element(estrategia, localizador)
        return elemento

    def encontrar_elementos (self, estrategia: bot.tipagem.ESTRATEGIAS_WEBELEMENT, localizador: str | Enum) -> list[WebElement] | None:
        """Encontrar elemento(s) na aba atual com base em um `localizador` para a `estrategia` selecionada"""
        localizador = localizador if isinstance(localizador, str) else str(localizador.value)
        bot.logger.debug(f"Procurando elementos no navegador ('{ estrategia }', '{ localizador }')")
        elementos = self.driver.find_elements(estrategia, localizador)
        return elementos if len(elementos) else None

    def hover_elemento (self, elemento: WebElement) -> None:
        """Realizar a ação de `hover` no `elemento`"""
        bot.logger.debug(f"Realizando ação de hover no elemento '{ elemento }'")
        ActionChains(self.driver).move_to_element(elemento).perform()


class Edge (Navegador):
    """Navegador Edge"""
    
    driver: WebDriverEdge
    """Driver Edge"""

    def __init__ (self, timeout=30.0):
        """Inicializar o navegador Edge
        - `timeout` utilizado na espera do `implicitly_wait`"""
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option('excludeSwitches', ['enable-logging']) # desativar prints
        options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.default_directory": rf"{ bot.windows.diretorio_execucao().caminho }\downloads",
        })
        
        self.driver = WebDriverEdge(options)
        self.driver.implicitly_wait(timeout)

        bot.logger.informar("Navegador Edge iniciado")


class Chrome (Navegador):
    """Navegador Edge"""
    
    driver: WebDriverChrome
    """Driver Chrome"""
    
    def __init__ (self, timeout=30.0):
        """Inicializar o navegador Chrome
        - `timeout` utilizado na espera do `implicitly_wait`"""
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option('excludeSwitches', ['enable-logging']) # desativar prints
        options.add_experimental_option("prefs", {
            "download.prompt_for_download": False,
            "download.default_directory": rf"{ bot.windows.diretorio_execucao().caminho }\downloads",
        })
        
        self.driver = WebDriverChrome(options)
        self.driver.implicitly_wait(timeout)

        bot.logger.informar("Navegador Chrome iniciado")


# TODO - O pesquisar não está retornando e o código pausa
# Checar se colocar o Driver no PATH faz diferença
class Explorer (Navegador):
    """Navegador Internet Explorer"""

    driver: WebDriverIe
    """Driver Internet Explorer"""

    def __init__ (self, timeout=30.0):
        """Inicializar o navegador Edge no modo Internet Explorer
        - `timeout` utilizado na espera do `implicitly_wait`"""
        options = IeOptions()
        options.attach_to_edge_chrome = True
        options.add_argument("--ignore-certificate-errors")
        
        self.driver = WebDriverIe(options)
        self.driver.maximize_window()
        self.driver.implicitly_wait(timeout)

        bot.logger.informar("Navegador Edge, modo Internet Explorer, iniciado")


__all__ = [
    "Edge",
    "Chrome",
    "Explorer"
]
