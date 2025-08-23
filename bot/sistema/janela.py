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

class Dialogo:
    """Diálogo do windows para confirmação"""

    elemento: ElementoW32

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} {self.elemento}>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento

    @property
    def texto (self) -> str:
        """Texto dos descendentes, exceto dos botões, concatenados por `; `"""
        return "; ".join(
            elemento.texto
            for elemento in self.elemento.to_uia().descendentes(aguardar=0.5)
            if elemento.texto and not elemento.botao
        )

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

    def negar (self) -> None:
        """Negar o diálogo clicando nas opções `("nao", "ok", "no")`
        - Checado se fechou corretamente"""
        botoes = ("nao", "ok", "no")
        hwnd = self.elemento.hwnd
        self.elemento\
            .encontrar(lambda e: bot.util.normalizar(e.texto) in botoes)\
            .clicar()
        assert bot.util.aguardar_condicao(lambda: not win32gui.IsWindow(hwnd), timeout=3),\
            "Diálogo não fechou conforme esperado"

    def confirmar (self) -> None:
        """Confirmar o diálogo clicando nas opções `("sim", "ok", "yes")`
        - Checado se fechou corretamente"""
        botoes = ("sim", "ok", "yes")
        hwnd = self.elemento.hwnd
        self.elemento\
            .encontrar(lambda e: bot.util.normalizar(e.texto) in botoes)\
            .clicar()
        assert bot.util.aguardar_condicao(lambda: not win32gui.IsWindow(hwnd), timeout=3),\
            "Diálogo não fechou conforme esperado"

class Popup (Dialogo):
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
        self.elemento.aguardar(5).sleep(0.1)

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

    @typing.overload
    def __getitem__[T: ElementoW32] (self: T, value: int | str) -> T: ...
    @typing.overload
    def __getitem__[T: ElementoW32] (self: T, value: tuple[int, ...]) -> list[T]: ...
    def __getitem__[T: ElementoW32] (self: T, value: object) -> T | list[T]:
        """Obter elemento(s) filho(s) ordenado(s) pela coordenada
        - `int` index
        - `str` texto ou class_name
        - `(int, ...)` + de 1 index"""
        filhos = self.janela.ordernar_elementos_coordenada(
            self.filhos(aguardar=5)
        )
        match value:
            case str() as texto:
                try: return next(filho for filho in filhos
                                 if texto.lower() in (filho.class_name.lower(), filho.texto.lower()))
                except StopIteration:
                    raise Exception(f"Filho do elemento na {self.janela} não encontrado com texto ou class_name '{texto}'")

            case int() as index:
                try: return filhos[index]
                except IndexError:
                    raise IndexError(f"Filho do elemento na {self.janela} não encontrado no index '{index}'")

            case tuple() as indexes if all(isinstance(index, int) for index in indexes):
                try: return [filhos[index] for index in indexes]
                except IndexError:
                    raise IndexError(f"Filhos do elemento na {self.janela} não encontrados nos índices '{indexes}'")

            case _:
                raise ValueError(f"Tipo {type(value)} inesperado ao se obter elemento")

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
        return (
            win32gui.IsWindowVisible(self.hwnd) == 1
            and bool(self.coordenada)
        )

    @property
    def ativo (self) -> bool:
        return win32gui.IsWindowEnabled(self.hwnd) == 1

    @property
    def caixa_selecao (self) -> CaixaSelecaoW32:
        """Obter a interface da caixa de seleção de uma `CheckBox`
        - O Elemento pode não aceitar caso não seja uma `CheckBox`, necessário teste"""
        return CaixaSelecaoW32(self)

    def filhos[T: ElementoW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool] | None = None,
                                         aguardar: int | float = 0) -> list[T]:
        """Elementos filhos imediatos
        - `filtro` para escolher os filhos. `Default: visíveis`
        - `aguardar` tempo em segundos para aguardar por algum filho"""
        assert aguardar >= 0, "Tempo para aguardar por filhos deve ser >= 0"

        filhos = list[T]()
        Elemento = type(self)
        filtro = filtro or (lambda e: e.visivel)

        def callback (hwnd, _) -> bool:
            if win32gui.GetParent(hwnd) == self.hwnd:
                try:
                    e = Elemento(hwnd, self.janela, self, self.profundidade + 1)
                    if filtro(e): filhos.append(e)
                except Exception: pass
            return True

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or (not filhos and cronometro() < aguardar):
            primeiro = False
            try: win32gui.EnumChildWindows(self.hwnd, callback, None)
            except Exception: pass

        return filhos

    def descendentes[T: ElementoW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool] | None = None,
                                               aguardar: int | float = 0) -> list[T]:
        """Todos os elementos descendentes
        - `filtro` para escolher os descendentes. `Default: visíveis`
        - `aguardar` tempo em segundos para aguardar por algum descendente"""
        assert aguardar >= 0, "Tempo para aguardar por descendentes deve ser >= 0"

        descendentes = list[T]()
        filtro = filtro or (lambda e: e.visivel)

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or (not descendentes and cronometro() < aguardar):
            primeiro = False

            for filho in self.filhos():
                try:
                    if filtro(filho): descendentes.append(filho)
                except Exception: pass
                descendentes.extend(filho.descendentes(filtro))

        return descendentes

    def encontrar[T: ElementoW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool],
                                            aguardar: int | float = 0) -> T:
        """Encontrar o primeiro elemento descendente, com a menor profundidade, de acordo com o `filtro`
        - `aguardar` tempo em segundos para aguardar pelo elemento
        - `AssertionError` caso não encontre"""
        assert aguardar >= 0, "Tempo para aguardar por elemento deve ser >= 0"

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or cronometro() < aguardar:
            primeiro = False

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
                      virtual: bool = True,
                      focar: bool = True) -> typing.Self:
        """Clicar com o `botão` no centro do elemento
        - `virtual` indica se o click deve ser simulado ou feito com o mouse de fato
        - `focar` indicador se dever ser feito o foco no elemento
        - Apenas alguns elementos aceitam clicks virtuais"""
        if focar: self.focar()
        coordenada = self.coordenada

        if virtual:
            lparam = win32api.MAKELONG(coordenada.largura // 2, coordenada.altura // 2)
            down, up, wparam = BOTOES_VIRTUAIS_MOUSE[botao]
            win32gui.PostMessage(self.hwnd, down, wparam, lparam)
            win32gui.PostMessage(self.hwnd, up, 0, lparam)
        else: bot.mouse.mover(coordenada).clicar(botao=botao)

        return self.aguardar().sleep(0.1)

    def apertar (self, *teclas: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO,
                       focar: bool = True) -> typing.Self:
        """Apertar e soltar as `teclas` uma por vez
        - `focar` indicador se dever ser feito o foco no elemento"""
        if focar: self.focar()
        for tecla in teclas:
            bot.teclado.apertar(tecla)
            self.aguardar()
        return self.sleep(0.1)

    def digitar (self, texto: str,
                       virtual: bool = True,
                       focar: bool = True) -> typing.Self:
        """Digitar o `texto` no elemento
        - `virtual` indica se deve ser simulado ou feito com o teclado de fato
        - `virtual` substitui o texto atual pelo `texto`
        - `focar` indicador se dever ser feito o foco no elemento
        - Apenas alguns elementos aceitam o `virtual`"""
        if focar: self.focar()
        if virtual: win32gui.SendMessage(self.hwnd, win32con.WM_SETTEXT, 0, texto) # type: ignore
        else: bot.teclado.digitar(texto)
        return self.aguardar().sleep(0.1)

    def atalho (self, *teclas: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO) -> typing.Self:
        """Pressionar as teclas sequencialmente e soltá-las em ordem reversa"""
        self.focar()
        bot.teclado.atalho(*teclas)
        return self.aguardar().sleep(0.1)

    def scroll (self, quantidade: int = 1, direcao: bot.tipagem.DIRECOES_SCROLL = "baixo") -> typing.Self:
        """Realizar scroll no elemento `quantidade` vezes na `direção`"""
        assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"

        self.focar()
        bot.mouse.mover(self.coordenada)
        for _ in range(quantidade):
            bot.mouse.scroll_vertical(direcao=direcao)
            self.aguardar()

        return self.sleep(0.1)

    def print_arvore (self) -> None:
        """Realizar o `print()` da árvore de elementos"""
        def print_nivel (elemento: ElementoW32, prefixo: str) -> None:
            prefixo += "|   " if elemento.profundidade > self.profundidade else ""
            print(prefixo, elemento, sep="")
            for filho in elemento.filhos(lambda e: True):
                print_nivel(filho, prefixo)

        print_nivel(self, "")

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
        return (
            self.uiaelement.CurrentIsOffscreen == 0
            and bool(self.coordenada)
        )

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
        """Checar se o elemento é um botão"""
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

    def filhos (self, filtro: typing.Callable[[ElementoUIA], bot.tipagem.SupportsBool] | None = None,
                      aguardar: int | float = 0) -> list[ElementoUIA]:
        assert aguardar >= 0, "Tempo para aguardar por filhos deve ser >= 0"

        filhos = []
        filtro = filtro or (lambda e: e.visivel)
        finder: uiaclient.IUIAutomationElementArray = self.uiaelement.FindAll(
            uiaclient.TreeScope_Children,
            ElementoUIA.UIA.CreateTrueCondition()
        )

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or (not filhos and cronometro() < aguardar):
            primeiro = False

            for i in range(finder.Length):
                filho: uiaclient.IUIAutomationElement = finder.GetElement(i)
                e = ElementoUIA(filho.CurrentNativeWindowHandle, self.janela, self, filho, self.profundidade + 1)
                try:
                    if filtro(e): filhos.append(e)
                except Exception: pass

        return filhos

    def focar (self) -> typing.Self:
        if not self.janela.focada:
            self.janela.focar()
        self.uiaelement.SetFocus()
        return self.aguardar()

    def clicar (self, botao: bot.tipagem.BOTOES_MOUSE = "left",
                      virtual: bool = True,
                      focar: bool = True) -> typing.Self:
        """Clicar com o `botão` no centro do elemento
        - `virtual` indica se o click deve ser simulado ou feito com o mouse de fato
        - Apenas alguns elementos aceitam clicks virtuais"""
        if focar: self.focar()
        invocavel = self.invocavel

        if virtual and invocavel and botao == "left": invocavel.Invoke()
        else: super().clicar(botao, virtual, focar)

        return self.aguardar()

    def digitar (self, texto: str,
                       virtual: bool = True,
                       focar: bool = True) -> typing.Self:
        if focar: self.focar()
        value = self.query_interface(uiaclient.UIA_ValuePatternId, uiaclient.IUIAutomationValuePattern)

        if virtual and value: value.SetValue(texto)
        else: super().digitar(texto, virtual, focar)

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

    ### Criação
    ```
    JanelaW32.from_foco()                                       # Janela focada
    JanelaW32(lambda j: "titulo" in j.titulo and j.visivel)     # Procurar a janela com filtro dinâmico
    JanelaW32(lambda j: ..., aguardar=10)                       # Aguardar por 10 segundos até encontrar a janela
    JanelaW32.iniciar("notepad", shell=True, aguardar=30)       # Iniciar uma janela via novo processo
    ```

    ### Importante
    - Utilizar sempre o `.visivel` nos filtros para garantir que a `janela/elemento` está aparecendo
    - Utilizar `.focar()` após obter uma janela para trazer para frente e aguardar estar responsível
    - Utilizar o `.aguardar()` para aguardar a janela/elemento estar responsível
        - Utilizado pelo `.focar()`
        - Utilizado pelos métodos de interação dos elementos

    ### Propriedades
    ```
    janela.titulo
    janela.class_name
    janela.visivel    # Checar se a janela está visível
    janela.coordenada # Região na tela da janela
    janela.processo   # Processo do módulo `psutil` para controle via `PID`
    janela.focada     # Checar se a janela está em primeiro plano
    janela.minimizada
    janela.maximizada
    janela.fechada
    ```

    ### Elementos
    ```
    # Elemento superior da janela para acessar, procurar e manipular elementos
    elemento = janela.elemento
    elemento.filhos()           # Filhos imediatos
    elemento.descendentes()     # Todos os elementos
    elemento.encontrar(...)     # Encontrar o primeiro elemento descendente de acordo com o `filtro`
    elemento.clicar("left")     # Clicar com o `botão` no centro do elemento
    elemento.digitar("texto")   # Digitar o `texto` no elemento
    # Encontrar ordenando pela posição Y e X
    primeiro = elemento[0]              # Obter elemento pelo index
    primeiro, ultimo = elemento[0, -1]  # Obter elementos pelo index
    elemento["texto ou class_name"]     # Obter elemento pelo texto ou class_name
    ...
    ```

    ### Métodos
    ```
    janela.maximizar()
    janela.minimizar()
    janela.focar()              # Trazer a janela para primeiro plano
    janela.aguardar()           # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
    janela.sleep()              # Aguardar por `segundos` até continuar a execução
    janela.janelas_processo()   # Janelas do mesmo processo da `janela`
    janela.janela_processo(...) # Obter janela do mesmo processo da `janela` de acordo com o `filtro`
    janela.print_arvore()       # Realizar o `print()` da árvore de elementos da janela e das janelas do processo
    ```

    ### Métodos acessores
    ```
    janela.to_uia()     # Obter uma instância da `JanelaW32` como `JanelaUIA`
    janela.dialogo()    # Encontrar janela de diálogo com `class_name`
    janela.popup()      # Encontrar janela de popup com `class_name`
    ```

    ### Métodos destrutores
    ```
    janela.fechar()     # Enviar a mensagem de fechar para janela e retornar indicador se fechou corretamente
    janela.destruir()   # Enviar a mensagem de destruir para janela e retornar indicador se fechou corretamente
    janela.encerrar()   # Enviar a mensagem de fechar para janela e encerrar pelo processo caso não feche
    ```

    ### Métodos estáticos
    ```
    JanelaW32.titulos_janelas_visiveis()                  # Obter os títulos das janelas visíveis
    JanelaW32.ordernar_elementos_coordenada(elementos=[]) # Ordenar os `elementos` pela posição Y e X
    ```
    """

    hwnd: int

    def __init__[T: JanelaW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool],
                                         aguardar: int | float = 0) -> None:
        assert aguardar >= 0, "Tempo para aguardar por janela deve ser >= 0"

        encontrados: list[T] = []
        def callback (hwnd: int, _) -> bool:
            j = self.from_hwnd(hwnd)
            try:
                if filtro(j): encontrados.append(j) # type: ignore
            except Exception: pass
            return True

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or (not encontrados and cronometro() < aguardar):
            primeiro = False
            try: win32gui.EnumWindows(callback, None)
            except Exception: pass

        match encontrados:
            case []: raise Exception(f"Janela não encontrada para o filtro informado")
            # Apenas 1
            case [janela]: self.hwnd = janela.hwnd
            # > 1 | Ordenar pelos que não possuem parente, visíveis e com mais filhos
            case _: self.hwnd = sorted(
                encontrados,
                key = lambda janela: (
                    1 if win32gui.GetParent(janela.hwnd) == 0 else 0,
                    1 if (elemento := janela.elemento).visivel else 0,
                    len(elemento.filhos())
                )
            )[-1].hwnd

    @classmethod
    def from_hwnd[T: JanelaW32] (cls: type[T], hwnd: int) -> T:
        janela = object.__new__(cls)
        janela.hwnd = hwnd
        return janela

    @classmethod
    def from_foco[T: JanelaW32] (cls: type[T]) -> T:
        """Obter a janela com o foco do sistema"""
        hwnd = win32gui.GetForegroundWindow()
        return cls.from_hwnd(hwnd)

    @classmethod
    def iniciar[T: JanelaW32] (cls: type[T], *argumentos: str, shell: bool = True, aguardar: int | float = 30) -> T:
        """Iniciar uma janela no sistema a partir dos `argumentos`
        - Alguns aplicativos podem abrir mais de uma janela, utilizar o `self.janelas_processo()` para verificar"""
        titulos_antes = JanelaW32.titulos_janelas_visiveis()
        processo = bot.sistema.abrir_processo(*argumentos, shell=shell)

        try:
            returncode = bot.estruturas.Resultado(processo.wait, 1).valor_ou(None)
            assert returncode in (None, 0), f"Processo finalizado com erro | returncode({returncode})"
            bot.util.aguardar_condicao(
                lambda: titulos_antes.symmetric_difference(JanelaW32.titulos_janelas_visiveis()),
                timeout = aguardar,
                delay = 0.5
            )
            return cls(
                lambda j: j.titulo and j.visivel
                                   and j.titulo not in titulos_antes,
                aguardar = aguardar
            ).focar()

        except Exception as erro:
            raise AssertionError(f"Falha ao iniciar uma janela com os argumentos '{" ".join(argumentos)}' | {erro}")

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} '{self.titulo}' class_name='{self.class_name}'>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento

    def __hash__ (self) -> int:
        return hash(self.hwnd)

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
        """Região na tela da janela"""
        return self.elemento.coordenada
    @property
    def visivel (self) -> bool:
        """Checar se a janela está visível
        - Importante utilização nos filtros para não interagir com a janela cedo demais"""
        return self.elemento.visivel

    @functools.cached_property
    def elemento (self) -> ElementoW32:
        """Elemento superior da janela para acessar, procurar e manipular elementos"""
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
        return self.aguardar().sleep(0.1)

    @property
    def minimizada (self) -> bool:
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMINIMIZED
    def minimizar (self) -> typing.Self:
        win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)
        return self.aguardar().sleep(0.1)

    @property
    def focada (self) -> bool:
        """Checar se a janela está em primeiro plano"""
        return win32gui.GetForegroundWindow() == self.hwnd
    def focar (self) -> typing.Self:
        """Trazer a janela para primeiro plano"""
        if self.minimizada:
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            bot.util.aguardar_condicao(lambda: self.visivel, timeout=5, delay=0.5)

        flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        def trazer_para_o_foco () -> bool:
            try:
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
                win32gui.SetForegroundWindow(self.hwnd)
                return self.focada
            except Exception: return False
        focado = bot.util.aguardar_condicao(trazer_para_o_foco, timeout=5)

        # O Windows pode não permitir
        # Clicando em cima da janela resolve
        if not focado:
            bot.mouse.mover(self.coordenada.topo()).clicar()
            trazer_para_o_foco()

        return self.aguardar().sleep(0.1)

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

    def janelas_processo[T: JanelaW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool] | None = None) -> list[T]:
        """Janelas do mesmo processo da `janela`
        - `filtro` para escolher as janelas. `Default: visível e ativo`"""
        self.aguardar()
        encontrados: list[T] = []
        filtro = filtro or (lambda j: j.visivel and j.elemento.ativo)

        def callback (hwnd, _) -> typing.Literal[True]:
            if hwnd == self.hwnd: return True
            j = self.from_hwnd(hwnd)

            try:
                if j.processo.pid == self.processo.pid and filtro(j):
                    encontrados.append(j)
            except Exception: pass
            return True

        try: win32gui.EnumWindows(callback, None)
        except Exception: pass
        return encontrados

    def janela_processo[T: JanelaW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool],
                                                aguardar: int | float = 0) -> T:
        """Obter janela do mesmo processo da `janela` de acordo com o `filtro`
        - `aguardar` tempo em segundos para aguardar por alguma janela"""
        self.aguardar()
        assert aguardar >= 0, "Tempo para aguardar por janela deve ser >= 0"

        encontrados = list[T]()
        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or (not encontrados and cronometro() < aguardar):
            primeiro = False
            encontrados = self.janelas_processo(filtro)

        if not encontrados: raise Exception(f"Janela não encontrada no processo para o filtro informado")
        return encontrados[0]

    def dialogo (self, class_name: str = "#32770",
                       aguardar: int | float = 0) -> Dialogo | None:
        """Encontrar janela de diálogo com `class_name`
        - `None` caso não encontre
        - `aguardar` tempo em segundos para aguardar pelo diálogo"""
        assert aguardar >= 0, "Tempo para aguardar pelo diálogo deve ser >= 0"

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or cronometro() < aguardar:
            primeiro = False

            for filho in self.elemento.filhos(lambda e: e.class_name == class_name and e.ativo):
                return Dialogo(filho)
            for janela in self.janelas_processo(lambda j: j.class_name == class_name and j.elemento.ativo):
                return Dialogo(janela.elemento)

    def popup (self, class_name: str = "#32768",
                     aguardar: int | float = 0) -> Popup | None:
        """Encontrar janela de popup com `class_name`
        - `None` caso não encontre
        - `aguardar` tempo em segundos para aguardar pelo popup"""
        assert aguardar >= 0, "Tempo para aguardar pelo popup deve ser >= 0"

        primeiro, cronometro = True, bot.util.Cronometro()
        while primeiro or cronometro() < aguardar:
            primeiro = False

            for filho in self.elemento.filhos(lambda e: e.class_name == class_name and e.ativo):
                return Popup(filho)
            for janela in self.janelas_processo(lambda j: j.class_name == class_name and j.elemento.ativo):
                return Popup(janela.elemento)

    def print_arvore (self) -> None:
        """Realizar o `print()` da árvore de elementos da janela e das janelas do processo"""
        for janela in (self, *self.janelas_processo(lambda j: True)):
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

    ### Criação
    ```
    JanelaUIA.from_foco()                                   # Janela focada
    JanelaUIA(lambda j: "titulo" in j.titulo and j.visivel) # Procurar a janela com filtro dinâmico
    JanelaUIA(lambda j: ..., aguardar=10)                   # Aguardar por 10 segundos até encontrar a janela
    JanelaUIA.iniciar("notepad", shell=True, aguardar=30)   # Iniciar uma janela via novo processo
    ```

    ### Importante
    - Utilizar sempre o `.visivel` nos filtros para garantir que a `janela/elemento` está aparecendo
    - Utilizar `.focar()` após obter uma janela para trazer para frente
    - Utilizar o `.aguardar()` para aguardar a janela/elemento estar responsível
        - Utilizado pelo `.focar()`
        - Utilizado pelos métodos de interação dos elementos

    ### Propriedades
    ```
    janela.titulo
    janela.class_name
    janela.visivel    # Checar se a janela está visível
    janela.coordenada # Região na tela da janela
    janela.processo   # Processo do módulo `psutil` para controle via `PID`
    janela.focada     # Checar se a janela está em primeiro plano
    janela.minimizada
    janela.maximizada
    janela.fechada
    ```

    ### Elementos
    ```
    # Elemento superior da janela para acessar, procurar e manipular elementos
    elemento = janela.elemento
    elemento.filhos()           # Filhos imediatos
    elemento.descendentes()     # Todos os elementos
    elemento.encontrar(...)     # Encontrar o primeiro elemento descendente de acordo com o `filtro`
    elemento.clicar("left")     # Clicar com o `botão` no centro do elemento
    elemento.digitar("texto")   # Digitar o `texto` no elemento
    # Encontrar ordenando pela posição Y e X
    primeiro = elemento[0]              # Obter elemento pelo index
    primeiro, ultimo = elemento[0, -1]  # Obter elementos pelo index
    elemento["texto ou class_name"]     # Obter elemento pelo texto ou class_name
    ...

    # Específico UIA
    elemento.valor              # Propriedade `value` do elemento. Útil para inputs
    elemento.aba                # Checar se o elemento é uma aba
    elemento.barra_menu         # Checar se o elemento é uma barra de menu
    elemento.botao              # Checar se o elemento é um botão
    ...
    ```

    ### Métodos
    ```
    janela.maximizar()
    janela.minimizar()
    janela.focar()              # Trazer a janela para primeiro plano
    janela.aguardar()           # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
    janela.sleep()              # Aguardar por `segundos` até continuar a execução
    janela.janelas_processo()   # Janelas do mesmo processo da `janela`
    janela.janela_processo(...) # Obter janela do mesmo processo da `janela` de acordo com o `filtro`
    janela.print_arvore()       # Realizar o `print()` da árvore de elementos da janela e das janelas do processo

    # Específico UIA
    janela.menu("Arquivo", "Salvar") # Selecionar as `opções` nos menus
    ```

    ### Métodos acessores
    ```
    janela.dialogo()    # Encontrar janela de diálogo com `class_name`
    janela.popup()      # Encontrar janela de popup com `class_name`
    ```

    ### Métodos destrutores
    ```
    janela.fechar()     # Enviar a mensagem de fechar para janela e retornar indicador se fechou corretamente
    janela.destruir()   # Enviar a mensagem de destruir para janela e retornar indicador se fechou corretamente
    janela.encerrar()   # Enviar a mensagem de fechar para janela e encerrar pelo processo caso não feche
    ```

    ### Métodos estáticos
    ```
    JanelaUIA.titulos_janelas_visiveis()                  # Obter os títulos das janelas visíveis
    JanelaUIA.ordernar_elementos_coordenada(elementos=[]) # Ordenar os `elementos` pela posição Y e X
    ```
    """

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

    def menu (self, *opcoes: str) -> typing.Self:
        """Selecionar as `opções` nos menus
        - Procurado por elementos `barra_menu` com `item_barra_menu`"""
        self.focar()
        barras_menu_usadas = set[ElementoUIA]()
        barras_menu_nao_usadas = lambda: self.elemento.descendentes(
            lambda e: e.barra_menu and e not in barras_menu_usadas,
            aguardar = 2
        )

        # mover o mouse para o topo para não interferir
        bot.mouse.mover(self.coordenada.topo())

        for opcao in map(str.lower, opcoes):
            opcao_encontrada = False
            self.aguardar().sleep(0.2)

            for barra_menu in barras_menu_nao_usadas():
                barras_menu_usadas.add(barra_menu)
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
                    else: e.clicar(focar=False)

                    opcao_encontrada = True
                    break
                if opcao_encontrada: break

            assert opcao_encontrada, f"Opção '{opcao}' não encontrada nas barras de menu"

        return self.aguardar().sleep(0.1)

__all__ = [
    "JanelaUIA",
    "JanelaW32",
]