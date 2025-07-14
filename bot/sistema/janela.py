# std
from __future__ import annotations
import time, typing, functools
# interno
import bot
# externo
import psutil
import win32gui, win32con, win32api, win32process # pywin32
import comtypes.client
comtypes.client.GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient as uiaclient

BOTOES_VIRTUAIS_MOUSE = {
    "left":   (win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON),
    "middle": (win32con.WM_MBUTTONDOWN, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON),
    "right":  (win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON),
}

class Dialogo [T: ElementoW32 | ElementoUIA]:
    """Diálogo do windows para confirmação"""

    elemento: T

    def __init__ (self, elemento: T) -> None:
        self.elemento = elemento

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} {self.elemento}>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento

    def clicar (self, botao: str = "Não") -> bool:
        """Clicar no botão com o texto `botão`
        - Texto normalizado, então acentuação ou & não faz diferença
        - `AssertionError` caso não seja encontrado
        - Retornado indicador se o diálogo fechou corretamente"""
        hwnd = self.elemento.hwnd
        botao = bot.util.normalizar(botao)
        self.elemento\
            .encontrar(lambda e: botao in bot.util.normalizar(e.texto))\
            .clicar()
        return bot.util.aguardar_condicao(lambda: not win32gui.IsWindow(hwnd), timeout=3)

    def fechar (self, timeout: float | int = 10.0) -> bool:
        """Enviar a mensagem de fechar para o popup e retornar indicador se fechou corretamente"""
        hwnd = self.elemento.hwnd
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return bot.util.aguardar_condicao(lambda: not win32gui.IsWindow(hwnd), timeout)

class Popup[T: ElementoW32 | ElementoUIA] (Dialogo[T]):
    """Popup do windows"""

class CaixaSelecaoW32:
    """Classe para tratar a caixa de seleção do W32"""

    elemento: ElementoW32

    def __init__(self, elemento: ElementoW32) -> None:
        self.elemento = elemento

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} hwnd='{self.elemento.hwnd}'>"

    @property
    def selecionado (self) -> bool:
        """Checar se está selecionado"""
        estado = win32gui.SendMessage(self.elemento.hwnd, win32con.BM_GETCHECK, 0, 0)
        return estado == 1

    def alternar (self) -> None:
        """Alterar o estado da seleção
        - O `elemento.clicar()` pode ser preferencial caso elementos aguardando o evento não atualizem"""
        estado = 0 if self.selecionado else 1
        win32gui.SendMessage(self.elemento.hwnd, win32con.BM_CLICK, estado, 0)
        self.elemento.aguardar(5)

class ElementoW32:
    """Elemento para o backend Win32"""

    hwnd: int
    janela: JanelaW32
    profundidade: int
    parente: ElementoW32 | None

    def __init__ (self, hwnd: int,
                        janela: JanelaW32,
                        parente: ElementoW32 | None = None,
                        profundidade: int = 0) -> None:
        self.hwnd = int(hwnd or 0)
        self.janela = janela
        self.parente = parente
        self.profundidade = profundidade

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} hwnd='{self.hwnd}' texto='{self.texto}' class_name='{self.class_name}' profundidade='{self.profundidade}'>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and all(
            getattr(self, attr, 1) == getattr(value, attr, 2)
            for attr in ("hwnd", "profundidade", "class_name")
        )

    def __hash__ (self) -> int:
        return hash(repr(self))

    @property
    def texto (self) -> str:
        """Texto do elemento
        - Realizado `strip()` e removido o char `&` que pode vir a aparecer"""
        return win32gui.GetWindowText(self.hwnd).strip().replace("&", "")

    @functools.cached_property
    def class_name (self) -> str:
        return win32gui.GetClassName(self.hwnd) or ""

    @property
    def coordenada (self) -> bot.estruturas.Coordenada:
        box = win32gui.GetWindowRect(self.hwnd)
        return bot.estruturas.Coordenada.from_box(box)

    @property
    def visivel (self) -> bool:
        return win32gui.IsWindowVisible(self.hwnd) == 1

    @property
    def ativo (self) -> bool:
        return win32gui.IsWindowEnabled(self.hwnd) == 1

    @property
    def caixa_selecao (self) -> CaixaSelecaoW32:
        """Obter a interface da caixa de seleção de uma `CheckBox`
        - O Elemento pode não aceitar caso não seja uma `CheckBox`, necessário teste"""
        return CaixaSelecaoW32(self)

    def filhos (self, filtro: typing.Callable[[ElementoW32], bot.tipagem.SupportsBool] | None = None) -> list[ElementoW32]:
        """Elementos filhos de primeiro nível
        - `filtro` para escolher os filhos. `Default: visíveis`"""
        filhos = []
        filtro = filtro or (lambda e: e.visivel)

        def callback (hwnd, _) -> bool:
            if win32gui.GetParent(hwnd) == self.hwnd:
                try:
                    e = ElementoW32(hwnd, self.janela, self, self.profundidade + 1)
                    if filtro(e): filhos.append(e)
                except Exception: pass
            return True

        try: win32gui.EnumChildWindows(self.hwnd, callback, None)
        except Exception: pass

        return filhos

    def descendentes (self, filtro: typing.Callable[[ElementoW32], bot.tipagem.SupportsBool] | None = None) -> list[ElementoW32]:
        """Todos os elementos descendentes
        - `filtro` para escolher os descendentes. `Default: visíveis`"""
        descendentes = []
        filtro = filtro or (lambda e: e.visivel)

        for filho in self.filhos():
            try:
                if filtro(filho): descendentes.append(filho)
            except Exception: pass
            descendentes.extend(filho.descendentes(filtro))

        return descendentes

    def encontrar (self, filtro: typing.Callable[[ElementoW32], bot.tipagem.SupportsBool]) -> ElementoW32:
        """Encontrar o primeiro elemento descendente, com a menor profundidade, e de acordo com o `filtro`
        - `AssertionError` caso não encontre"""
        elementos = bot.estruturas.Deque(self.filhos())

        while elementos:
            elemento = elementos.popleft()
            try:
                if filtro(elemento): return elemento
            except Exception: pass
            elementos.extend(elemento.filhos())

        raise AssertionError("Nenhum elemento descendente encontrado para o filtro")

    def textos (self, separador=" | ") -> str:
        """Textos dos descendentes concatenados pelo `separador`"""
        return separador.join(
            d.texto
            for d in self.descendentes(lambda e: True)
            if d.texto
        )

    def sleep (self, segundos: int | float = 1) -> typing.Self:
        """Aguardar por `segundos` até continuar a execução"""
        time.sleep(segundos)
        return self

    def aguardar (self, timeout: float | int = 120.0) -> typing.Self:
        """Aguarda `timeout` segundos até que a thread da GUI fique ociosa"""
        if self is not self.janela.elemento:
            self.janela.aguardar()
        if self.janela.fechada or self.hwnd == 0:
            return self

        try: win32gui.SendMessageTimeout(self.hwnd, win32con.WM_NULL, None, None, win32con.SMTO_ABORTIFHUNG, int(timeout * 1000))
        except Exception: raise TimeoutError(f"O elemento não respondeu após '{timeout}' segundos esperando") from None
        return self

    def focar (self) -> typing.Self:
        if not self.janela.focada:
            self.janela.focar()

        try: win32gui.SetForegroundWindow(self.hwnd)
        except Exception: pass
        return self.aguardar()

    def clicar (self, botao: bot.tipagem.BOTOES_MOUSE = "left",
                      virtual: bool = True) -> typing.Self:
        """Clicar com o `botão` no centro do elemento
        - `virtual` indica se o click deve ser simulado ou feito com o mouse de fato
        - Apenas alguns elementos aceitam clicks virtuais"""
        self.focar()
        coordenada = self.coordenada

        if virtual:
            lparam = win32api.MAKELONG(coordenada.largura // 2, coordenada.altura // 2)
            down, up, wparam = BOTOES_VIRTUAIS_MOUSE[botao]
            win32gui.PostMessage(self.hwnd, down, wparam, lparam)
            win32gui.PostMessage(self.hwnd, up, 0, lparam)
        else:
            bot.mouse.clicar_mouse(botao, coordenada=coordenada)

        return self.aguardar()

    def apertar (self, *teclas: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO) -> typing.Self:
        """Apertar e soltar as `teclas` uma por vez"""
        self.focar()
        for tecla in teclas:
            bot.teclado.apertar_tecla(tecla)
            self.aguardar()
        return self

    def digitar (self, texto: str, virtual: bool = True) -> typing.Self:
        """Digitar o `texto` no elemento
        - `virtual` indica se deve ser simulado ou feito com o teclado de fato
        - `virtual` substitui o texto atual pelo `texto`
        - Apenas alguns elementos aceitam o `virtual`"""
        self.focar()
        if virtual: win32gui.SendMessage(self.hwnd, win32con.WM_SETTEXT, 0, texto) # type: ignore
        else: bot.teclado.digitar_teclado(texto)
        return self.aguardar()

    def atalho (self, *teclas: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO) -> typing.Self:
        """Apertar as `teclas` sequencialmente e depois soltá-las em ordem reversa"""
        self.focar()
        bot.teclado.atalho_teclado(teclas)
        return self.aguardar()

    def scroll (self, quantidade: int = 1, direcao: bot.tipagem.DIRECOES_SCROLL = "baixo") -> typing.Self:
        """Realizar scroll no elemento `quantidade` vezes na `direção`"""
        assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"

        self.focar()
        for _ in range(quantidade):
            bot.mouse.scroll_vertical(1, direcao, self.coordenada)
            self.aguardar()

        return self

    def print_arvore (self) -> None:
        """Realizar o `print()` da árvore de elementos"""
        def print_nivel (elemento: ElementoW32, prefixo="") -> None:
            prefixo += "|   " if elemento.profundidade > 0 else ""
            print(f"{prefixo}{elemento}")
            for filho in elemento.filhos(lambda e: True):
                print_nivel(filho, prefixo)

        print_nivel(self)

    def to_uia (self) -> ElementoUIA:
        """Criar um instância do `ElementoW32` como `ElementoUIA`"""
        return ElementoUIA(
            self.hwnd,
            self.janela.to_uia(),
            self.parente.to_uia() if self.parente else None,
            profundidade = self.profundidade
        )

class ElementoUIA (ElementoW32):
    """Elemento para o backend UIA"""

    janela: JanelaUIA
    profundidade: int
    parente: ElementoUIA | None
    uiaelement: uiaclient.IUIAutomationElement

    UIA = comtypes.client.CreateObject(
        progid = comtypes.GUID("{FF48DBA4-60EF-4201-AA87-54103EEF594E}"),
        interface = uiaclient.IUIAutomation
    ).QueryInterface(uiaclient.IUIAutomation)

    def __init__ (self, hwnd: int,
                        janela: JanelaUIA,
                        parente: ElementoUIA | None = None,
                        uiaelement: uiaclient.IUIAutomationElement | None = None,
                        profundidade: int = 0) -> None:
        self.hwnd = int(hwnd or 0)
        self.janela = janela # type: ignore
        self.parente = parente # type: ignore
        self.profundidade = profundidade
        self.uiaelement = uiaelement or ElementoUIA.UIA.ElementFromHandle(hwnd)

    @property
    def texto (self) -> str:
        return str(self.uiaelement.CurrentName or "").strip().replace("&", "")

    @functools.cached_property
    def class_name (self) -> str:
        return self.uiaelement.CurrentClassName or ""

    @property
    def coordenada (self) -> bot.estruturas.Coordenada:
        rect = self.uiaelement.CurrentBoundingRectangle
        return bot.estruturas.Coordenada(
            x = rect.left,
            y = rect.top,
            largura = rect.right - rect.left,
            altura = rect.bottom - rect.top,
        )

    @property
    def visivel (self) -> bool:
        return self.uiaelement.CurrentIsOffscreen == 0

    @property
    def ativo (self) -> bool:
        return self.uiaelement.CurrentIsEnabled == 1

    @property
    def valor (self) -> str:
        """Propriedade `value` do elemento. Útil para inputs
        - Feito `strip()`"""
        try:
            value = self.query_interface(uiaclient.UIA_ValuePatternId, uiaclient.IUIAutomationValuePattern)
            return str(value.CurrentValue).strip() if value else ""
        except Exception: return ""

    @property
    def tipo (self) -> str:
        """Nome localizado do tipo do elemento"""
        try: return str(self.uiaelement.CurrentLocalizedControlType or "")
        except Exception: return ""

    @property
    def automation_id (self) -> str:
        try: return str(self.uiaelement.CurrentAutomationId or "")
        except Exception: return ""

    @property
    def teclas_atalho (self) -> list[str]:
        """Nome localizado do tipo do elemento"""
        try: return [
            tecla.lower()
            for tecla in map(str.strip, str(self.uiaelement.CurrentAccessKey).replace(",", "+").split("+"))
            if tecla
        ]
        except Exception: return []

    @property
    def expansivel (self) -> uiaclient.IUIAutomationExpandCollapsePattern | None:
        """Obter a interface de expandir se for `Lista ou ComboBox`
        - `None` caso o elemento não suporte expansão"""
        return self.query_interface(uiaclient.UIA_ExpandCollapsePatternId, uiaclient.IUIAutomationExpandCollapsePattern)

    @property
    def item_selecionavel (self) -> uiaclient.IUIAutomationSelectionItemPattern | None:
        """Obter a interface do item selecionável de uma `Lista ou ComboBox`
        - `None` caso o elemento não seja um item selecionável"""
        return self.query_interface(uiaclient.UIA_SelectionItemPatternId, uiaclient.IUIAutomationSelectionItemPattern)

    @property
    def grid (self) -> uiaclient.IUIAutomationGridPattern | None:
        """Obter a interface `Grid`
        - `None` caso o elemento não suporte o `Pattern`"""
        return self.query_interface(
            uiaclient.UIA_GridPatternId,
            uiaclient.IUIAutomationGridPattern
        )

    @property
    def table (self) -> uiaclient.IUIAutomationTablePattern | None:
        """Obter a interface `Table`
        - `None` caso o elemento não suporte o `Pattern`"""
        return self.query_interface(
            uiaclient.UIA_TablePatternId,
            uiaclient.IUIAutomationTablePattern
        )

    @property
    def caixa_selecao (self) -> uiaclient.IUIAutomationTogglePattern | None: # type: ignore
        """Obter a interface da caixa de seleção de uma `CheckBox`
        - `None` caso o elemento não seja uma caixa de seleção
        - `CurrentToggleState` para se obter o estado da caixa `desativado == 0` e `ativo == 1`
        - `Toggle()` para alterar o estado"""
        return self.query_interface(uiaclient.UIA_TogglePatternId, uiaclient.IUIAutomationTogglePattern)

    @property
    def invocavel (self) -> uiaclient.IUIAutomationInvokePattern | None:
        """Obter a interface para invocar o elemento, semelhante a um click
        - `None` caso o elemento não seja um item invocável"""
        return self.query_interface(uiaclient.UIA_InvokePatternId, uiaclient.IUIAutomationInvokePattern)

    @property
    def botao (self) -> bool:
        return self.uiaelement.CurrentControlType == uiaclient.UIA_ButtonControlTypeId

    @property
    def editavel (self) -> bool:
        return self.query_interface(uiaclient.UIA_ValuePatternId, uiaclient.IUIAutomationValuePattern) != None

    @property
    def barra_menu (self) -> bool:
        """Checar se o elemento é uma barra de menu"""
        menu_controls = (uiaclient.UIA_MenuBarControlTypeId, uiaclient.UIA_MenuControlTypeId)
        return self.uiaelement.CurrentControlType in menu_controls\
            or "windowedpopupclass" in self.class_name.lower()

    @property
    def item_barra_menu (self) -> bool:
        """Checar se o elemento é um item da barra de menu"""
        return self.uiaelement.CurrentControlType == uiaclient.UIA_MenuItemControlTypeId

    @property
    def aba (self) -> bool:
        """Checar se o elemento é uma aba"""
        return self.uiaelement.CurrentControlType == uiaclient.UIA_TabControlTypeId

    @property
    def item_aba (self) -> bool:
        """Checar se o elemento é um item de uma aba"""
        return self.uiaelement.CurrentControlType == uiaclient.UIA_TabItemControlTypeId

    def filhos (self, filtro: typing.Callable[[ElementoUIA], bot.tipagem.SupportsBool] | None = None) -> list[ElementoUIA]: # type: ignore
        filhos = []
        filtro = filtro or (lambda e: e.visivel)
        finder: uiaclient.IUIAutomationElementArray = self.uiaelement.FindAll(
            uiaclient.TreeScope_Children,
            ElementoUIA.UIA.CreateTrueCondition()
        )

        for i in range(finder.Length):
            filho: uiaclient.IUIAutomationElement = finder.GetElement(i)
            e = ElementoUIA(filho.CurrentNativeWindowHandle, self.janela, self, filho, self.profundidade + 1)
            try:
                if filtro(e): filhos.append(e)
            except Exception: pass

        return filhos

    def descendentes (self, filtro: typing.Callable[[ElementoUIA], bot.tipagem.SupportsBool] | None = None) -> list[ElementoUIA]: # type: ignore
        descendentes = []
        filtro = filtro or (lambda e: e.visivel)
        for filho in self.filhos():
            try:
                if filtro(filho): descendentes.append(filho)
            except Exception: pass
            descendentes.extend(filho.descendentes(filtro))
        return descendentes

    def encontrar (self, filtro: typing.Callable[[ElementoUIA], bot.tipagem.SupportsBool]) -> ElementoUIA:
        elementos = bot.estruturas.Deque(self.filhos())

        while elementos:
            elemento = elementos.popleft()
            try:
                if filtro(elemento): return elemento
            except Exception: pass
            elementos.extend(elemento.filhos())

        raise AssertionError("Nenhum elemento descendente encontrado para o filtro")

    def focar (self) -> typing.Self:
        if not self.janela.focada:
            self.janela.focar()
        self.uiaelement.SetFocus()
        return self.aguardar()

    def clicar (self, botao: bot.tipagem.BOTOES_MOUSE = "left",
                      virtual: bool = True) -> typing.Self:
        """Clicar com o `botão` no centro do elemento
        - `virtual` indica se o click deve ser simulado ou feito com o mouse de fato
        - Apenas alguns elementos aceitam clicks virtuais"""
        self.focar()
        invocavel = self.invocavel

        if virtual and invocavel and botao == "left": invocavel.Invoke()
        else: super().clicar(botao, virtual)

        return self.aguardar()

    def digitar (self, texto: str, virtual: bool = True) -> typing.Self:
        self.focar()
        value = self.query_interface(uiaclient.UIA_ValuePatternId, uiaclient.IUIAutomationValuePattern)

        if virtual and value: value.SetValue(texto)
        else: super().digitar(texto, virtual)

        return self.aguardar()

    def selecionar (self, texto: str) -> None:
        """Selecionar a opção que possua o `texto`
        - Elemento deve ser `expansivel` e conter `item_selecionavel`"""
        texto = texto.lower()
        expansivel = self.expansivel
        assert expansivel, f"Elemento não é expansível {self}"

        self.focar()
        expansivel.Expand()
        self.aguardar()

        self.encontrar(lambda e: e.item_selecionavel != None and texto in e.texto.lower())\
            .item_selecionavel\
            .Select() # type: ignore

        expansivel.Collapse()  
        self.aguardar() 

    def query_interface[T] (self, pattern_id: int, interface: type[T]) -> T | None:
        """Obter o `pattern_id` do `uiaelement` e realizar a query da `interface`
        - `None` caso o `uiaelement` não esteja de acordo com a `interface`"""
        try: return self.uiaelement\
                        .GetCurrentPattern(pattern_id)\
                        .QueryInterface(interface)
        except Exception: return None

    def listar_patterns (self) -> list[str]:
        """Lista os nomes dos patterns suportados pelo elemento"""
        patterns = []

        for nome in dir(uiaclient):
            if not nome.startswith("UIA_") or not nome.endswith("PatternId"):
                continue
            try:
                pattern_id = getattr(uiaclient, nome)
                if bool(self.uiaelement.GetCurrentPattern(pattern_id)):
                    patterns.append(nome)
            except Exception: pass

        return patterns

class JanelaW32:
    """Classe para manipulação de janelas e elementos para o backend Win32

    ```
    # criação, informar um filtro para buscar a janela
    JanelaW32(lambda j: "titulo" in j.titulo)
    JanelaW32(lambda j: "titulo" in j.titulo, aguardar=10) # Aguardar por 10 segundos até encontrar
    # criação, obter a janela focada
    JanelaW32.from_foco()
    # método estático para obter os títulos das janelas visíveis
    JanelaW32.titulos_janelas_visiveis()
    # janelas existentes que pertencem ao mesmo processo
    janela.janelas_processo()
    # visualizar a árvore da janela + as janelas do processo
    janela.print_arvore()
    # obter o dialogo do windows caso esteja aberto
    d = janela.dialogo()
    if d: d.clicar(botao="Sim")
    # obter o popup do windows caso esteja aberto
    p = janela.popup()
    if p: fechar()

    # elemento superior da janela com algumas propriedades e métodos de manipulação
    janela.elemento
    # procurar elementos de primeiro nível de acordo com o filtro
    janela.elemento.filhos(None ou lambda e: e.class_name == "classname")
    # procurar todos os elementos de acordo com o filtro
    janela.elemento.descendentes(None ou lambda e: e.class_name == "classname")
    # encontrar o elemento menos profundo de acordo com o filtro
    janela.elemento.encontrar(lambda e: e.class_name == "classname")
    ```
    """

    hwnd: int

    def __init__ (self, filtro: typing.Callable[[typing.Self], bot.tipagem.SupportsBool],
                        aguardar: int | float = 0) -> None:
        assert aguardar >= 0, "Tempo para aguardar por janela deve ser >= 0"

        encontrados: list[JanelaW32] = []
        def callback (hwnd: int, _) -> bool:
            j = JanelaW32.from_hwnd(hwnd)
            try:
                if filtro(j): encontrados.append(j) # type: ignore
            except Exception: pass
            return True

        primeiro, cronometro = True, bot.util.cronometro()
        while primeiro or (not encontrados and cronometro() < aguardar):
            primeiro = False
            try: win32gui.EnumWindows(callback, None)
            except Exception: pass

        match encontrados:
            case []: raise Exception(f"Janela não encontrada para o filtro informado")
            # Apenas 1
            case [janela]: self.hwnd = janela.hwnd
            # > 1 | Ordenar pelos que não possuem parente e com mais filhos
            case _: self.hwnd = sorted(
                encontrados,
                key = lambda janela: (
                    1 if win32gui.GetParent(janela.hwnd) == 0 else 0,
                    len(janela.elemento.filhos())
                )
            )[-1].hwnd

    @classmethod
    def from_hwnd (cls, hwnd: int) -> JanelaW32:
        janela = object.__new__(cls)
        janela.hwnd = hwnd
        return janela

    @classmethod
    def from_foco (cls) -> JanelaW32:
        """Obter a janela com o foco do sistema"""
        hwnd = win32gui.GetForegroundWindow()
        return JanelaW32.from_hwnd(hwnd)

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} '{self.titulo}' class_name='{self.class_name}'>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento
        
    def __hash__ (self) -> int:
        return hash(self.hwnd)

    def __bool__ (self) -> bool:
        return True

    @property
    def titulo (self) -> str:
        """Texto do elemento
        - Realizado `strip()` e removido o char `&` que pode vir a aparecer"""
        return win32gui.GetWindowText(self.hwnd).strip().replace("&", "")
    @property
    def class_name (self) -> str:
        return win32gui.GetClassName(self.hwnd) or ""
    @property
    def coordenada (self) -> bot.estruturas.Coordenada:
        return self.elemento.coordenada

    @functools.cached_property
    def elemento (self) -> ElementoW32:
        return ElementoW32(self.hwnd, self)
    @functools.cached_property
    def processo (self) -> psutil.Process:
        """Processo do módulo `psutil` para controle via `PID`"""
        _, pid = win32process.GetWindowThreadProcessId(self.hwnd)
        return psutil.Process(pid)

    @property
    def maximizada (self) -> bool:
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMAXIMIZED
    def maximizar (self) -> typing.Self:
        win32gui.ShowWindow(self.hwnd, win32con.SW_MAXIMIZE)
        return self

    @property
    def minimizada (self) -> bool:
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMINIMIZED
    def minimizar (self) -> typing.Self:
        win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)
        return self

    @property
    def focada (self) -> bool:
        return win32gui.GetForegroundWindow() == self.hwnd
    def focar (self) -> typing.Self:
        if self.aguardar().minimizada: win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        bot.util.aguardar_condicao(
            lambda: win32gui.SetForegroundWindow(self.hwnd) == None,
            timeout = 60
        )
        return self.aguardar()

    @property
    def fechada (self) -> bool:
        return not win32gui.IsWindow(self.hwnd)
    def fechar (self, timeout: float | int = 10.0) -> bool:
        """Enviar a mensagem de fechar para janela e retornar indicador se fechou corretamente"""
        win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        return bot.util.aguardar_condicao(lambda: self.fechada, timeout)
    def destruir (self, timeout: float | int = 10.0) -> bool:
        """Enviar a mensagem de destruir para janela e retornar indicador se fechou corretamente"""
        win32gui.PostMessage(self.hwnd, win32con.WM_DESTROY, 0, 0)
        if not self.fechada:
            win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
        return bot.util.aguardar_condicao(lambda: self.fechada, timeout)
    def encerrar (self, timeout: float | int = 10.0) -> None:
        """Enviar a mensagem de fechar para janela
        - Caso continue aberto após `timeout` segundos, será feito o encerramento pelo processo"""
        if not self.fechar(timeout):
            self.processo.kill()
            self.processo.wait(float(timeout))

    def sleep (self, segundos: int | float = 1) -> typing.Self:
        """Aguardar por `segundos` até continuar a execução"""
        time.sleep(segundos)
        return self
    def aguardar (self, timeout: float | int = 120.0) -> typing.Self:
        """Aguarda `timeout` segundos até que a thread da GUI fique ociosa"""
        if self.fechada or self.hwnd == 0: return self
        try: win32gui.SendMessageTimeout(self.hwnd, win32con.WM_NULL, None, None, win32con.SMTO_ABORTIFHUNG, int(timeout * 1000))
        except Exception: raise TimeoutError(f"A janela não respondeu após '{timeout}' segundos esperando") from None
        return self

    def janelas_processo (self, filtro: typing.Callable[[JanelaW32], bot.tipagem.SupportsBool] | None = None) -> list[JanelaW32]:
        """Janelas do mesmo processo da `janela` mas que estão fora de sua árvore
        - `filtro` para escolher as janelas. `Default: visível e ativo`"""
        encontrados: list[JanelaW32] = []
        filtro = filtro or (lambda j: j.elemento.visivel and j.elemento.ativo)

        def callback (hwnd, _) -> typing.Literal[True]:
            if hwnd == self.hwnd: return True
            j = JanelaW32.from_hwnd(hwnd)

            try:
                if j.processo.pid == self.processo.pid and filtro(j):
                    encontrados.append(j)
            except Exception: pass
            return True

        try: win32gui.EnumWindows(callback, None)
        except Exception: pass
        return encontrados

    def janela_processo (self, filtro: typing.Callable[[JanelaW32], bot.tipagem.SupportsBool],
                               aguardar: int | float = 0) -> JanelaW32:
        """Janela do mesmo processo da `janela` mas que está fora de sua árvore
        - `filtro` para escolher as janelas
        - `aguardar` tempo em segundos para aguardar por alguma janela"""
        assert aguardar >= 0, "Tempo para aguardar por janela deve ser >= 0"

        encontrados = list[JanelaW32]()
        primeiro, cronometro = True, bot.util.cronometro()
        while primeiro or (not encontrados and cronometro() < aguardar):
            primeiro = False
            encontrados = self.janelas_processo(filtro)

        if not encontrados: raise Exception(f"Janela não encontrada no processo para o filtro informado")
        return encontrados[0]

    def dialogo (self, class_name: str = "#32770",
                       aguardar: int | float = 0) -> Dialogo[ElementoW32] | None:
        """Encontrar janela de diálogo com `class_name`
        - `None` caso não encontre
        - `aguardar` tempo em segundos para aguardar pelo diálogo"""
        assert aguardar >= 0, "Tempo para aguardar pelo diálogo deve ser >= 0"

        primeiro, cronometro = True, bot.util.cronometro()
        while primeiro or cronometro() < aguardar:
            primeiro = False

            for filho in self.elemento.filhos():
                if filho.class_name == class_name:
                    return Dialogo(filho)

            for janela in self.janelas_processo():
                if janela.class_name == class_name:
                    return Dialogo(janela.elemento)

    def popup (self, class_name: str = "#32768",
                     aguardar: int | float = 0) -> Popup[ElementoW32] | None:
        """Encontrar janela de popup com `class_name`
        - `None` caso não encontre
        - `aguardar` tempo em segundos para aguardar pelo popup"""
        assert aguardar >= 0, "Tempo para aguardar pelo popup deve ser >= 0"

        primeiro, cronometro = True, bot.util.cronometro()
        while primeiro or cronometro() < aguardar:
            primeiro = False

            for filho in self.elemento.filhos():
                if filho.class_name == class_name:
                    return Popup(filho)

            for janela in self.janelas_processo():
                if janela.class_name == class_name:
                    return Popup(janela.elemento)

    def print_arvore (self) -> None:
        """Realizar o `print()` da árvore de elementos da janela e das janelas do processo"""
        for janela in (self, *self.janelas_processo()):
            janela.elemento.print_arvore()
            print()

    def to_uia (self) -> JanelaUIA:
        """Obter uma instância da `JanelaW32` como `JanelaUIA`"""
        return JanelaUIA.from_hwnd(self.hwnd)

    @staticmethod
    def titulos_janelas_visiveis () -> set[str]:
        encontrados = set()
        def callback (hwnd: int, _) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                titulo = win32gui.GetWindowText(hwnd).strip().replace("&", "")
                if titulo: encontrados.add(titulo)
            return True

        try: win32gui.EnumWindows(callback, None)
        except Exception: pass

        return encontrados

    @staticmethod
    def ordernar_elementos_coordenada[T: ElementoW32 | ElementoUIA] (elementos: list[T], margem=5) -> list[T]:
        """Ordenar os `elementos` pela posição Y e X
        - Agrupa o Y com a `margem` de pixels
        - Alteração `In-place`, retornado a mesma lista de `elementos`"""
        y_atual: int | None = None
        grupo_linhas: list[list[T]] = []

        def nova_linha (y: int) -> bool:
            return y_atual == None or y > y_atual + margem

        # agrupar por linhas
        for elemento in sorted(elementos, key=lambda e: e.coordenada.y):
            y = elemento.coordenada.y
            if nova_linha(y): y_atual = y; grupo_linhas.append([elemento])
            else: grupo_linhas[-1].append(elemento)

        # ordenar os grupos pelo x
        for grupo in grupo_linhas:
            grupo.sort(key = lambda e: e.coordenada.x)

        # alterar in-place
        elementos.clear()
        for grupo in grupo_linhas:
            elementos.extend(grupo)

        return elementos

class JanelaUIA (JanelaW32):
    """Classe para manipulação de janelas e elementos para o backend UIA
    ```
    # criação, informar um filtro para buscar a janela
    JanelaUIA(lambda j: "titulo" in j.titulo)
    # criação, obter a janela focada
    JanelaUIA.from_foco()
    # método estático para obter os títulos das janelas visíveis
    JanelaUIA.titulos_janelas_visiveis()
    # janelas existentes que pertencem ao mesmo processo
    janela.janelas_processo()
    # visualizar a árvore da janela + as janelas do processo
    janela.print_arvore()
    # obter o dialogo do windows caso esteja aberto
    d = janela.dialogo()
    if d: d.clicar(botao="Sim")
    # obter o popup do windows caso esteja aberto
    p = janela.popup()
    if p: fechar()
    # abrir um menu da janela
    janela.menu("Arquivo", "Salvar")

    # elemento superior da janela com algumas propriedades e métodos de manipulação
    janela.elemento
    # procurar elementos de primeiro nível de acordo com o filtro
    janela.elemento.filhos(None ou lambda e: e.class_name == "classname")
    # procurar todos os elementos de acordo com o filtro
    janela.elemento.descendentes(None ou lambda e: e.class_name == "classname")
    # encontrar o elemento menos profundo de acordo com o filtro
    janela.elemento.encontrar(lambda e: e.class_name == "classname")
    ```
    """

    @classmethod
    def from_hwnd (cls, hwnd: int) -> JanelaUIA:
        janela = object.__new__(cls)
        janela.hwnd = hwnd
        return janela

    @classmethod
    def from_foco (cls) -> JanelaUIA:
        hwnd = win32gui.GetForegroundWindow()
        return cls.from_hwnd(hwnd)

    @functools.cached_property
    def elemento (self) -> ElementoUIA:
        return ElementoUIA(self.hwnd, self)

    @property
    def maximizada (self) -> bool:
        pattern = self.elemento.query_interface(uiaclient.UIA_WindowPatternId, uiaclient.IUIAutomationWindowPattern)
        if not pattern: return False
        return pattern.CurrentWindowVisualState == uiaclient.WindowVisualState_Maximized
    def maximizar (self) -> typing.Self:
        pattern = self.elemento.query_interface(uiaclient.UIA_WindowPatternId, uiaclient.IUIAutomationWindowPattern)
        if pattern: pattern.SetWindowVisualState(uiaclient.WindowVisualState_Maximized)
        else: super().maximizar()
        return self

    @property
    def minimizada (self) -> bool:
        pattern = self.elemento.query_interface(uiaclient.UIA_WindowPatternId, uiaclient.IUIAutomationWindowPattern)
        if not pattern: return not self.fechada
        return pattern.CurrentWindowVisualState == uiaclient.WindowVisualState_Minimized
    def minimizar (self) -> typing.Self:
        pattern = self.elemento.query_interface(uiaclient.UIA_WindowPatternId, uiaclient.IUIAutomationWindowPattern)
        if pattern: pattern.SetWindowVisualState(uiaclient.WindowVisualState_Minimized)
        else: super().minimizar()
        return self

    def popup (self, class_name="#32768") -> Popup[ElementoUIA] | None: # type: ignore
        for filho in self.elemento.filhos():
            if filho.class_name == class_name:
                return Popup(filho)

        for janela in self.janelas_processo():
            if janela.class_name == class_name:
                return Popup(janela.elemento)

    def dialogo (self, class_name="#32770") -> Dialogo[ElementoUIA] | None: # type: ignore
        for filho in self.elemento.filhos():
            if filho.class_name == class_name:
                return Dialogo(filho)

        for janela in self.janelas_processo():
            if janela.class_name == class_name:
                return Dialogo(janela.elemento)

    def menu (self, *opcoes: str) -> typing.Self:
        """Selecionar as `opções` nos menus
        - Procurado por elementos `barra_menu` com `item_barra_menu`"""
        self.focar()
        barras_menu_usadas = set[ElementoUIA]()
        barras_menu_nao_usadas = lambda: self.elemento.descendentes(lambda e: e.barra_menu and e not in barras_menu_usadas)

        for index, opcao in enumerate(map(str.lower, opcoes)):
            opcao_encontrada = False
            if index > 0: bot.util.aguardar_condicao(lambda: barras_menu_nao_usadas(), 2)

            for barra_menu in barras_menu_nao_usadas():
                finder: uiaclient.IUIAutomationElementArray = barra_menu.uiaelement.FindAll(
                    # SubTree pega todos os itens da barra que o Children não consegue
                    uiaclient.TreeScope_Subtree,
                    ElementoUIA.UIA.CreateTrueCondition()
                )

                for i in range(finder.Length):
                    filho: uiaclient.IUIAutomationElement = finder.GetElement(i)
                    e = ElementoUIA(filho.CurrentNativeWindowHandle, self, barra_menu, filho, barra_menu.profundidade + 1)
                    if not e.item_barra_menu or opcao != e.texto.lower():
                        continue

                    if (expansivel := e.expansivel)\
                        and expansivel.Expand() != -1\
                        and expansivel.CurrentExpandCollapseState > 0: pass
                    elif invocavel := e.invocavel: invocavel.Invoke()
                    else: e.clicar()

                    opcao_encontrada = True
                    break

                if opcao_encontrada:
                    self.aguardar()
                    barras_menu_usadas.add(barra_menu)
                    break

            assert opcao_encontrada, f"Opção '{opcao}' não encontrada nas barras de menu"

        return self

    def janelas_processo (self, filtro: typing.Callable[[JanelaUIA], bot.tipagem.SupportsBool] | None = None) -> list[JanelaUIA]: # type: ignore
        encontrados: list[JanelaUIA] = []
        filtro = filtro or (lambda j: j.elemento.visivel and j.elemento.ativo)

        def callback (hwnd, _) -> typing.Literal[True]:
            if hwnd == self.hwnd: return True
            j = JanelaUIA.from_hwnd(hwnd)

            try:
                if j.processo.pid == self.processo.pid and filtro(j):
                    encontrados.append(j)
            except Exception: pass
            return True

        try: win32gui.EnumWindows(callback, None)
        except Exception: pass
        return encontrados

    def janela_processo (self, filtro: typing.Callable[[JanelaUIA], bot.tipagem.SupportsBool],
                               aguardar: int | float = 0) -> JanelaUIA:
        assert aguardar >= 0, "Tempo para aguardar por janela deve ser >= 0"

        encontrados = list[JanelaUIA]()
        primeiro, cronometro = True, bot.util.cronometro()
        while primeiro or (not encontrados and cronometro() < aguardar):
            primeiro = False
            encontrados = self.janelas_processo(filtro)

        if not encontrados: raise Exception(f"Janela não encontrada no processo para o filtro informado")
        return encontrados[0]

__all__ = [
    "JanelaUIA",
    "JanelaW32",
]