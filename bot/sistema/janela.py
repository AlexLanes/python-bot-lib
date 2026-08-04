# std
from __future__ import annotations
from types import UnionType
import time, typing, functools, contextlib
# interno
import bot
from bot.estruturas import String
# externo
import psutil
import win32gui, win32con, win32api, win32process # pywin32
import comtypes.client
comtypes.client.GetModule('UIAutomationCore.dll')
from comtypes.gen import UIAutomationClient as uiaclient

TABELA_SUBSTITUICAO_CHARS = str.maketrans({
    "&": "", # remove &
    "\r": "" # remove \r
})
BOTOES_VIRTUAIS_MOUSE = {
    "left":   (win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON),
    "middle": (win32con.WM_MBUTTONDOWN, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON),
    "right":  (win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP, win32con.MK_RBUTTON),
}

class Dialogo:
    """Diálogo do windows para confirmação"""

    elemento: ElementoUIA
    texto: str
    """Texto dos descendentes, exceto dos botões, concatenados por `; `"""

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento.to_uia().sleep(0.25)
        self.texto = "; ".join(
            texto
            for elemento in self.elemento.descendentes(aguardar=0.5)
            if (texto := elemento.texto) and not elemento.tipo.botao
        )

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} {self.elemento}>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento

    def aguardar_fechar (self, timeout: float = 5) -> bool:
        """Aguardar o diálogo fechar por `timeout` segundos e retornar o indicador"""
        return bot.tempo.aguardar(
            lambda: not win32gui.IsWindow(self.elemento.hwnd)
                    or not self.elemento.visivel,
            timeout = timeout
        )

    def fechar (self, timeout: float = 10.0) -> bool:
        """Enviar a mensagem de fechar para o diálogo e retornar indicador se fechou corretamente"""
        try: win32gui.PostMessage(self.elemento.hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception: pass
        return self.aguardar_fechar(timeout)

    def clicar (self, botao: str = "Não") -> bool:
        """Clicar no botão com o texto `botão`
        - Texto normalizado, então acentuação ou & não faz diferença
        - `AssertionError` caso não seja encontrado
        - Retornado indicador se o diálogo fechou corretamente"""
        botao = String(botao).normalizar()
        self.elemento\
            .encontrar(lambda e: botao in String(e.texto).normalizar())\
            .clicar()
        return self.aguardar_fechar()

    def negar (self) -> typing.Self:
        """Negar o diálogo clicando nas opções `("nao", "ok", "no")`
        - Checado se fechou corretamente"""
        botoes = ("nao", "ok", "no")
        self.elemento\
            .encontrar(lambda e: String(e.texto).normalizar() in botoes)\
            .clicar()
        assert self.aguardar_fechar(3), "Diálogo não fechou conforme esperado"
        return self

    def confirmar (self) -> typing.Self:
        """Confirmar o diálogo clicando nas opções `("sim", "ok", "yes")`
        - Checado se fechou corretamente"""
        botoes = ("sim", "ok", "yes")
        self.elemento\
            .encontrar(lambda e: String(e.texto).normalizar() in botoes)\
            .clicar()
        assert self.aguardar_fechar(3), "Diálogo não fechou conforme esperado"
        return self

    def Raise (self, prefixo="Diálogo inesperado encontrado:", Error=Exception) -> typing.Never:
        raise Error(f"{prefixo.rstrip()} `{self.texto}`")

class Popup:
    """Popup do windows com opções"""

    elemento: ElementoUIA

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento.to_uia()

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} texto='{self.elemento.texto}' class_name='{self.elemento.class_name}'>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento

    def fechar (self, timeout: float | int = 10.0) -> bool:
        """Enviar a mensagem de fechar para o popup e retornar um indicador se fechou corretamente"""
        hwnd = self.elemento.hwnd
        try: win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except Exception: pass
        return bot.tempo.aguardar(lambda: not win32gui.IsWindow(hwnd), timeout)

    def itens_menu (self) -> list[ElementoUIA]:
        """Elementos do popup que são `item_barra_menu`"""
        return self.elemento.aguardar().descendentes(lambda e: e.tipo.item_barra_menu)

    def clicar (self, opcao: str) -> typing.Self:
        """Clicar no item de menu com o texto `opção`"""
        opcao = String(opcao).normalizar()
        elemento, *_ = [
            item
            for item in self.itens_menu()
            if opcao in String(item.texto)
        ] or [None]

        assert elemento is not None, f"Nenhum item no popup encontrado com a opção '{opcao}'"
        elemento.clicar(focar=False)

        return self

class CheckBox:

    elemento: ElementoUIA

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento.to_uia()

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} hwnd='{self.elemento.hwnd}'>"

    @property
    def selecionado (self) -> bool:
        """Checar se está selecionado"""
        if (toggle := self.elemento.pattern.toggle) is not None:
            return toggle.CurrentToggleState == 1
        return win32gui.SendMessage(self.elemento.hwnd, win32con.BM_GETCHECK, 0, 0) == 1

    def alternar (self) -> None:
        """Alterar o estado da seleção
        - O `clicar()` pode ser preferencial caso elementos aguardando o evento não atualizem"""
        toggle = self.elemento.pattern.toggle
        if toggle is not None: toggle.Toggle()
        else: win32gui.SendMessage(self.elemento.hwnd, win32con.BM_CLICK, 0, 0)
        self.elemento.sleep(0.1).aguardar(5)

    def clicar (self) -> typing.Self:
        self.elemento.clicar()
        return self

    def selecionar (self) -> None:
        """Selecionar o `CheckBox` se estiver desmarcado"""
        if not self.selecionado:
            self.alternar()

    def desmarcar (self) -> None:
        """Desmarcar o `CheckBox` se estiver selecionado"""
        if self.selecionado:
            self.alternar()

class GroupBox:

    elemento: ElementoUIA

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento.to_uia().aguardar()

    def opcoes (self, selecionados: bool | None = None) -> list[str]:
        """Opções existentes
        - `selecionados` para filtrar apenas pelos selecionados ou não"""
        return [
            texto
            for filho in self.elemento.filhos()
            if (texto := filho.texto) and (
                selecionados is None
                or filho.checkbox.selecionado == selecionados
            )
        ]

    def selecionar (self, *opcoes: str) -> None:
        """Selecionar as `opções` se estiverem desmarcados"""
        for filho in self.elemento.filhos(lambda e: e.texto in opcoes):
            filho.checkbox.selecionar()

    def desmarcar (self, *opcoes: str) -> None:
        """Desmarcar as `opções` se estiverem selecionados"""
        for filho in self.elemento.filhos(lambda e: e.texto in opcoes):
            filho.checkbox.desmarcar()

class RadioGroup:

    elemento: ElementoUIA

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento.to_uia().aguardar()

    @property
    def selecionado (self) -> str:
        """Opção selecionada
        - `""` caso nenhum selecionado"""
        for filho in self.elemento.filhos():
            if pattern := filho.pattern.item_selecionavel:
                if pattern.CurrentIsSelected: return filho.texto
            elif win32gui.SendMessage(filho.hwnd, win32con.BM_GETCHECK, 0, 0) == 1:
                return filho.texto
        return ""

    def opcoes (self) -> list[str]:
        """Opções existentes"""
        return [
            texto
            for filho in self.elemento.filhos()
            if (texto := filho.texto)
        ]

    def selecionar (self, opcao: str) -> None:
        """Selecionar a `opção`"""
        elemento = self.elemento // opcao
        if (pattern := elemento.pattern.item_selecionavel) is not None:
            pattern.Select()
        else: win32gui.SendMessage(elemento.hwnd, win32con.BM_CLICK, 0, 0)

class ListControl:

    elemento: ElementoUIA

    def __init__ (self, elemento: ElementoW32) -> None:
        self.elemento = elemento.to_uia().aguardar()

    @property
    def multipla_selecao (self) -> bool:
        """Checar se aceita múltipla seleção"""
        if (selecionavel := self.elemento.pattern.selecionavel) is not None:
            return selecionavel.CurrentCanSelectMultiple == 1
        return False

    @property
    def opcoes (self) -> list[str]:
        """Opções existentes"""
        return [
            filho.texto
            for filho in self.elemento.filhos()
            if filho.tipo.item_lista
        ]

    @property
    def selecionados (self) -> list[str]:
        return [
            filho.texto
            for filho in self.elemento.filhos()
            if (item := filho.pattern.item_selecionavel) and item.CurrentIsSelected
        ]

    def selecionar (self, *opcoes: str) -> None:
        """Selecionar as `opções`
        - Apenas 1 aceito quando não aceita múltipla seleção"""
        multiplo = self.multipla_selecao
        if not multiplo and len(opcoes) > 1:
            raise ValueError("A lista não permite múltipla seleção")

        for opcao in opcoes:
            elemento = self.elemento / opcao
            selecionavel = elemento.pattern.item_selecionavel
            assert selecionavel is not None, f"Elemento Nome='{opcao}' não é um item selecionável"

            if not selecionavel.CurrentIsSelected:
                if multiplo: selecionavel.AddToSelection()
                else: selecionavel.Select()

class ElementoW32:
    """Elemento para o backend Win32"""

    hwnd: int
    janela: JanelaW32
    profundidade: int

    def __init__ (self, hwnd: int,
                        janela: JanelaW32,
                        profundidade: int = 0) -> None:
        self.hwnd = int(hwnd or 0)
        self.janela = janela
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
    def __getitem__ (self, value: int) -> typing.Self: ...
    @typing.overload
    def __getitem__ (self, value: tuple[int, ...]) -> list[typing.Self]: ...
    def __getitem__ (self, value: object) -> typing.Self | list[typing.Self]:
        """Obter elemento filho, visível e ativo, ordenado pela coordenada
        - `int` -> `index`
        - `(int, ...)` -> n `index`"""
        filhos = self.janela.ordernar_elementos_coordenada(
            self.aguardar().filhos(
                lambda e: e.visivel and e.ativo,
                aguardar = 1
            )
        )

        match value:
            case int() as index:
                try: return filhos[index]
                except IndexError:
                    raise IndexError(f"Elemento filho não encontrado no {index=}")

            case tuple() as indexes if all(isinstance(index, int) for index in indexes):
                try: return [filhos[index] for index in indexes]
                except IndexError:
                    raise IndexError(f"Elementos filhos não encontrados em {indexes=}")

            case _:
                raise ValueError(f"Tipo {type(value)} inesperado ao se obter elemento")

    def __truediv__ (self, nome: str) -> typing.Self:
        """Obter elemento filho visível e ativo
        - Possível de utilizar index no fim do nome `[0]`
        - Operador `/`"""
        index: int | None = None
        if -1 not in (l := nome.find("["), r := nome.find("]", l)):
            index = int(nome[l + 1 : r])
            nome = nome[0 : l]

        elementos = self.janela.ordernar_elementos_coordenada(
            self.aguardar().filhos(
                lambda e:
                    e.visivel and e.ativo
                    and (
                        nome in String(e.class_name)
                        or nome in String(e.texto)
                    ),
                aguardar = 1
            )
        )

        if not elementos:
            raise Exception(f"Nenhum elemento filho {nome=} encontrado")
        if index is None and len(elementos) > 1:
            raise Exception(f"Múltiplas opções encontradas para o elemento filho {nome=}. Utilizar index para restringir '{nome}[0]'")

        try: return elementos[index or 0]
        except IndexError:
            raise IndexError(f"Elemento filho {nome=} não encontrado no {index=}")

    def __floordiv__ (self, nome: str) -> typing.Self:
        """Obter elemento descendente visível e ativo
        - Possível de utilizar index no fim do nome `[0]`
        - Operador `//`"""
        index: int | None = None
        if -1 not in (l := nome.find("["), r := nome.find("]", l)):
            index = int(nome[l + 1 : r])
            nome = nome[0 : l]

        elementos = self.janela.ordernar_elementos_coordenada(
            self.aguardar().descendentes(
                lambda e:
                    e.visivel and e.ativo
                    and (
                        nome in String(e.class_name)
                        or nome in String(e.texto)
                    ),
                aguardar = 1
            )
        )

        if not elementos:
            raise Exception(f"Nenhum elemento descendente {nome=} encontrado")
        if index is None and len(elementos) > 1:
            raise Exception(f"Múltiplas opções encontradas para o elemento descendente {nome=}. Utilizar index para restringir '{nome}[0]'")

        try: return elementos[index or 0]
        except IndexError:
            raise IndexError(f"Elemento descendente {nome=} não encontrado no {index=}")

    def __gt__ (self, nome: str) -> list[typing.Self]:
        """Obter elementos filhos visível e ativo
        - Operador `>`"""
        return self.janela.ordernar_elementos_coordenada(
            self.aguardar().filhos(
                lambda e:
                    e.visivel and e.ativo
                    and (
                        nome in String(e.class_name)
                        or nome in String(e.texto)
                    ),
                aguardar = 1
            )
        )

    def __rshift__ (self, nome: str) -> list[typing.Self]:
        """Obter elementos descendentes visível e ativo
        - Operador `>>`"""
        return self.janela.ordernar_elementos_coordenada(
            self.aguardar().descendentes(
                lambda e:
                    e.visivel and e.ativo
                    and (
                        nome in String(e.class_name)
                        or nome in String(e.texto)
                    ),
                aguardar = 1
            )
        )

    def __lshift__ (self, profundidade: int) -> typing.Self:
        """Obter o elemento parente subindo a `profundidade`
        - Operador `<<`"""
        assert profundidade >= 1
        assert profundidade <= self.profundidade, f"Profundidade desejada '{profundidade}' maior que o nível atual '{self.profundidade}'"

        elemento = self
        while profundidade > 0:
            profundidade -= 1
            elemento = elemento.parente
        return elemento # type: ignore

    def __xor__ (self, profundidade: int) -> typing.Self:
        """Obter o elemento parente subindo até a `profundidade`
        - Operador `^`"""
        assert profundidade >= 0, f"Profundidade desejada '{profundidade}' inválida"
        assert profundidade <= self.profundidade, f"Profundidade desejada '{profundidade}' maior que a atual '{self.profundidade}'"

        elemento = self
        while elemento.profundidade != profundidade:
            elemento = elemento.parente
        return elemento # type: ignore

    def __matmul__ (self, nome: str) -> JanelaW32:
        """Obter uma janela interna"""
        return self.janela @ nome

    @property
    def parente (self) -> ElementoW32:
        """Elemento na árvore de elementos que `self` é filho
        - `AssertionError` caso `profundidade==0`"""
        assert self.profundidade != 0, "Tentado obter o parente de um elemento de profundidade 0"
        return ElementoW32(
            win32gui.GetAncestor(self.hwnd, 1),
            self.janela,
            self.profundidade - 1
        )

    @property
    def texto (self) -> str:
        """Texto do elemento
        - Realizado `strip()` e removido o chars `(&, \\r)`"""
        return (
            win32gui.GetWindowText(self.hwnd)
            .strip()
            .translate(TABELA_SUBSTITUICAO_CHARS)
        )

    @functools.cached_property
    def class_name (self) -> str:
        return win32gui.GetClassName(self.hwnd) or ""

    @property
    def coordenada (self) -> bot.estruturas.Coordenada:
        box = win32gui.GetWindowRect(self.hwnd)
        return bot.estruturas.Coordenada.FromBox(box)

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
    def checkbox (self) -> CheckBox:
        """Obter a interface de uma `CheckBox`
        - Elemento pode não aceitar"""
        return CheckBox(self)

    @property
    def groupbox (self) -> GroupBox:
        """Obter a interface de um grupo de `CheckBox`
        - Elemento deve possui filhos `CheckBox`
        - Elemento pode não aceitar"""
        return GroupBox(self)

    @property
    def radiogroup (self) -> RadioGroup:
        """Obter a interface de um grupo de `RadioButton`
        - Elemento deve possui filhos `RadioButton`
        - Elemento pode não aceitar"""
        return RadioGroup(self)

    @property
    def listcontrol (self) -> ListControl:
        """Obter a interface de uma `List`
        - Elemento deve possui filhos `ListItem`
        - Elemento pode não aceitar"""
        return ListControl(self)

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
                    e = Elemento(hwnd, self.janela, self.profundidade + 1)
                    if filtro(e): filhos.append(e)
                except Exception: pass
            return True

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or (not filhos and cronometro < aguardar):
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

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or (not descendentes and cronometro < aguardar):
            primeiro = False

            for filho in self.filhos(lambda e: True):
                try:
                    if filtro(filho): descendentes.append(filho)
                except Exception: pass
                descendentes.extend(filho.descendentes(filtro))

        return descendentes

    def encontrar[T: ElementoW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool],
                                            aguardar: int | float = 0,
                                            msg_erro: str | None = None) -> T:
        """Encontrar o primeiro elemento descendente, com a menor profundidade, de acordo com o `filtro`
        - `aguardar` tempo em segundos para aguardar pelo elemento
        - `AssertionError(msg_erro)` caso não encontre"""
        assert aguardar >= 0, "Tempo para aguardar por elemento deve ser >= 0"

        filtro_todos = lambda e: True
        primeiro, cronometro = True, bot.tempo.Cronometro()

        while primeiro or cronometro < aguardar:
            primeiro = False

            elementos = bot.estruturas.Deque(self.filhos(filtro_todos))
            while elementos:
                elemento = elementos.popleft()
                try:
                    if filtro(elemento): return elemento
                except Exception: pass
                elementos.extend(elemento.filhos(filtro_todos))

        raise AssertionError(msg_erro or "Nenhum elemento descendente encontrado para o filtro")

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
            self.janela.aguardar(timeout)
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
                      focar: bool = True) -> typing.Self:
        """Clicar virtualmente com o `botão` no centro do elemento
        - `focar` indicador se dever ser feito o foco no elemento
        - Elemento pode não aceitar"""
        if focar: self.focar()
        coordenada = self.coordenada

        lparam = win32api.MAKELONG(coordenada.largura // 2, coordenada.altura // 2)
        down, up, wparam = BOTOES_VIRTUAIS_MOUSE[botao]
        win32gui.PostMessage(self.hwnd, down, wparam, lparam)
        win32gui.PostMessage(self.hwnd, up, 0, lparam)

        return self.sleep(0.01).aguardar()

    def input (self, texto: str, focar: bool = True) -> typing.Self:
        """Substituir o texto do elemento pelo `texto`
        - `focar` indicador se dever ser feito o foco no elemento
        - Elemento pode não aceitar"""
        if focar: self.focar()
        win32gui.SendMessage(self.hwnd, win32con.WM_SETTEXT, 0, texto) # type: ignore
        return self.sleep(0.01).aguardar()

    def tab (self) -> typing.Self:
        """Simular um `TAB` para notificar o elemento"""
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_TAB, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, win32con.VK_TAB, 0)
        return self.sleep(0.01).aguardar()

    def __or__ (self, texto: str) -> typing.Self:
        """Realizar o `input(texto)` com o `tab()`
        - Operador `|`"""
        return self.input(texto).tab()

    def enter (self) -> typing.Self:
        """Simular um `ENTER` para notificar o elemento"""
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        return self.sleep(0.01).aguardar()

    def limpar (self) -> typing.Self:
        """Limpar o texto do elemento
        - Elemento pode não aceitar"""
        win32gui.SendMessage(self.hwnd, win32con.WM_SETTEXT, 0, None)
        return self.sleep(0.01).aguardar()

    def clicar_mouse (self, botao: bot.tipagem.BOTOES_MOUSE = "left",
                            focar: bool = True,
                            xOffset = 0.5,
                            yOffset = 0.5) -> typing.Self:
        """Clicar com o `botão` do mouse no elemento
        - `focar` indicador se dever ser feito o foco no elemento
        - `xOffset` `yOffset` usado para transformar a posição `Default: Centro`"""
        if focar: self.focar()

        posicao = self.coordenada.transformar(xOffset, yOffset)
        bot.mouse.mover(posicao).clicar(botao=botao)

        return self.sleep(0.01).aguardar()

    def teclar (self, *teclas: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO,
                       focar: bool = True) -> typing.Self:
        """Apertar e soltar as `teclas` uma por vez
        - `focar` indicador se dever ser feito o foco no elemento"""
        if focar: self.focar()
        for tecla in teclas:
            bot.teclado.apertar(tecla)
            self.aguardar()
        return self.sleep(0.01).aguardar()

    def teclar_n (self, tecla: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO,
                        n: int,
                        focar: bool = True) -> typing.Self:
        """Apertar e soltar a `tecla` `n` vezes
        - `focar` indicador se dever ser feito o foco no elemento"""
        if focar: self.focar()
        for _ in range(max(n, 1)):
            bot.teclado.apertar(tecla)
            self.aguardar()
        return self.sleep(0.01).aguardar()

    def digitar (self, texto: str, focar: bool = True) -> typing.Self:
        """Digitar o `texto` no elemento
        - `focar` indicador se dever ser feito o foco no elemento"""
        if focar: self.focar()
        bot.teclado.digitar(texto)
        return self.sleep(0.01).aguardar()

    def atalho (self, *teclas: bot.tipagem.char | bot.tipagem.BOTOES_TECLADO,
                      focar: bool = True) -> typing.Self:
        """Pressionar as teclas sequencialmente e soltá-las em ordem reversa
        - `focar` indicador se dever ser feito o foco no elemento"""
        if focar: self.focar()
        bot.teclado.atalho(*teclas)
        return self.sleep(0.01).aguardar()

    def scroll (self, quantidade: int = 1,
                      direcao: bot.tipagem.DIRECOES_SCROLL = "baixo",
                      focar: bool = True) -> typing.Self:
        """Realizar scroll no elemento `quantidade` vezes na `direção`
        - `focar` indicador se dever ser feito o foco no elemento"""
        assert quantidade >= 1, "Quantidade de scrolls deve ser pelo menos 1"

        if focar: self.focar()
        bot.mouse.mover(self.coordenada)
        for _ in range(quantidade):
            bot.mouse.scroll_vertical(direcao=direcao)
            self.aguardar()

        return self.sleep(0.01).aguardar()

    def encontrar_cor (
            self,
            cor: bot.tipagem.rgb,
            modo: typing.Literal["primeiro", "ultimo", "media"] = "media"
        ) -> tuple[int, int] | None:
        """Encontrar a posição `(x, y)` de um pixel que tenha a `cor` rgb
        - Necessário dependência `[imagem]`
        - Corrigido a posição retornada da imagem para a tela
        - `None` caso não encontrado"""
        from bot.imagem import capturar_tela

        coordenada = self.focar().coordenada
        if posicao := capturar_tela(coordenada).encontrar_cor(cor, modo):
            c = self.coordenada
            return (
                posicao[0] + c.x,
                posicao[1] + c.y
            )

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
            self.profundidade,
            self.uiaelement if isinstance(self, ElementoUIA) else None
        )

class TiposUIA:
    def __init__ (self, elemento: ElementoUIA) -> None:
        self.e = elemento

    @property
    def nome (self) -> str:
        """Nome do tipo do elemento"""
        try: return str(self.e.uiaelement.CurrentControlType or "")
        except Exception: return ""

    @property
    def nome_localizado (self) -> str:
        """Nome localizado do tipo do elemento"""
        try: return str(self.e.uiaelement.CurrentLocalizedControlType or "")
        except Exception: return ""

    @property
    def botao (self) -> bool:
        """Checar se o elemento é um botão"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_ButtonControlTypeId

    @property
    def botao_radio (self) -> bool:
        """Checar se o elemento é um radio button"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_RadioButtonControlTypeId

    @property
    def checkbox (self) -> bool:
        """Checar se o elemento é um checkbox"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_CheckBoxControlTypeId

    @property
    def combobox (self) -> bool:
        """Checar se o elemento é um combobox"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_ComboBoxControlTypeId

    @property
    def barra_menu (self) -> bool:
        """Checar se o elemento é uma barra de menu"""
        menu_controls = (uiaclient.UIA_MenuBarControlTypeId, uiaclient.UIA_MenuControlTypeId)
        return self.e.uiaelement.CurrentControlType in menu_controls\
            or "windowedpopupclass" in self.e.class_name.lower()

    @property
    def item_barra_menu (self) -> bool:
        """Checar se o elemento é um item da barra de menu"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_MenuItemControlTypeId

    @property
    def aba (self) -> bool:
        """Checar se o elemento é uma aba"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_TabControlTypeId

    @property
    def item_aba (self) -> bool:
        """Checar se o elemento é um item de uma aba"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_TabItemControlTypeId

    @property
    def lista (self) -> bool:
        """Checar se o elemento é uma lista"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_ListControlTypeId

    @property
    def item_lista (self) -> bool:
        """Checar se o elemento é um item de uma lista"""
        return self.e.uiaelement.CurrentControlType == uiaclient.UIA_ListItemControlTypeId

class PatternsUIA:
    def __init__ (self, elemento: ElementoUIA) -> None:
        self.e = elemento

    @property
    def valor (self) -> uiaclient.IUIAutomationValuePattern | None:
        """Obter a interface para obter e alterar o valor de um elemento
        - `None` caso o elemento não suporte expansão"""
        return self.query(uiaclient.UIA_ValuePatternId, uiaclient.IUIAutomationValuePattern)

    @property
    def expansivel (self) -> uiaclient.IUIAutomationExpandCollapsePattern | None:
        """Obter a interface de expandir se for `Lista ou ComboBox`
        - `None` caso o elemento não suporte expansão"""
        return self.query(uiaclient.UIA_ExpandCollapsePatternId, uiaclient.IUIAutomationExpandCollapsePattern)

    @property
    def selecionavel (self) -> uiaclient.IUIAutomationSelectionPattern | None:
        """Obter a interface selecionável usado em `Lista`
        - `None` caso o elemento não seja selecionável"""
        return self.query(uiaclient.UIA_SelectionPatternId, uiaclient.IUIAutomationSelectionPattern)

    @property
    def item_selecionavel (self) -> uiaclient.IUIAutomationSelectionItemPattern | None:
        """Obter a interface do item selecionável de uma `Item Lista` `ComboBox` `RadioButton`
        - `None` caso o elemento não seja um item selecionável"""
        return self.query(uiaclient.UIA_SelectionItemPatternId, uiaclient.IUIAutomationSelectionItemPattern)

    @property
    def toggle (self) -> uiaclient.IUIAutomationTogglePattern | None:
        """Obter a interface usada em elementos com estado `ON` `OFF`
        - `None` caso o elemento não seja uma caixa de seleção
        - `CurrentToggleState` para se obter o estado da caixa `desativado == 0` e `ativo == 1`
        - `Toggle()` para alterar o estado"""
        return self.query(uiaclient.UIA_TogglePatternId, uiaclient.IUIAutomationTogglePattern)

    @property
    def invocavel (self) -> uiaclient.IUIAutomationInvokePattern | None:
        """Obter a interface para invocar o elemento, semelhante a um left click
        - `None` caso o elemento não seja um item invocável"""
        return self.query(uiaclient.UIA_InvokePatternId, uiaclient.IUIAutomationInvokePattern)

    @property
    def window (self) -> uiaclient.IUIAutomationWindowPattern | None:
        """Obter a interface para modificar a janela
        - `None` caso o elemento não seja um item invocável"""
        return self.query(uiaclient.UIA_WindowPatternId, uiaclient.IUIAutomationWindowPattern)

    def query[T] (self, pattern_id: int, interface: type[T]) -> T | None:
        """Obter o `pattern_id` do `uiaelement` e realizar a query da `interface`
        - `None` caso o `uiaelement` não esteja de acordo com a `interface`"""
        try: return self.e.uiaelement\
                        .GetCurrentPattern(pattern_id)\
                        .QueryInterface(interface)
        except Exception: return None

    def print (self) -> None:
        """Realizar o print dos nomes dos patterns suportados pelo elemento"""
        for nome in dir(uiaclient):
            if not nome.startswith("UIA_") or not nome.endswith("PatternId"):
                continue
            try:
                pattern_id = getattr(uiaclient, nome)
                if bool(self.e.uiaelement.GetCurrentPattern(pattern_id)):
                    print(nome)
            except Exception: pass

class ElementoUIA (ElementoW32):
    """Elemento para o backend UIA"""

    hwnd: int
    janela: JanelaUIA
    profundidade: int
    uiaelement: uiaclient.IUIAutomationElement

    UIA = comtypes.client.CreateObject(
        progid = comtypes.GUID("{FF48DBA4-60EF-4201-AA87-54103EEF594E}"),
        interface = uiaclient.IUIAutomation
    ).QueryInterface(uiaclient.IUIAutomation)

    def __init__ (self, hwnd: int,
                        janela: JanelaUIA,
                        profundidade: int = 0,
                        uiaelement: uiaclient.IUIAutomationElement | None = None) -> None:
        self.hwnd = int(hwnd or 0)
        self.janela = janela # type: ignore
        self.profundidade = profundidade
        self.uiaelement = uiaelement or ElementoUIA.UIA.ElementFromHandle(hwnd)

    def __eq__ (self, value: object) -> bool:
        return (
            isinstance(value, type(self))
            and super().__eq__(value)
            and self.uiaelement == value.uiaelement
        )

    def __hash__ (self) -> int:
        try: return hash(self.uiaelement.GetRuntimeId())
        except Exception: return super().__hash__()

    @property
    def parente (self) -> ElementoUIA:
        assert self.profundidade > 0, "Tentado obter o parente de um elemento de profundidade 0"
        element = self.UIA.ControlViewWalker.GetParentElement(self.uiaelement)
        return ElementoUIA(
            element.CurrentNativeWindowHandle,
            self.janela,
            self.profundidade - 1,
            element,
        )

    @property
    def texto (self) -> str:
        return (
            str(self.uiaelement.CurrentName or "")
            .strip()
            .translate(TABELA_SUBSTITUICAO_CHARS)
        )

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
            valor = self.pattern.valor
            return str(valor.CurrentValue).strip() if valor is not None else ""
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
    def tipo (self) -> TiposUIA:
        """Tipos de controle UIA"""
        return TiposUIA(self)

    @property
    def pattern (self) -> PatternsUIA:
        """Patterns de controles UIA"""
        return PatternsUIA(self)

    def __matmul__ (self, nome: str) -> JanelaUIA:
        """Obter uma janela interna"""
        return self.janela @ nome

    def filhos (self, filtro: typing.Callable[[ElementoUIA], bot.tipagem.SupportsBool] | None = None,
                      aguardar: int | float = 0) -> list[ElementoUIA]:
        assert aguardar >= 0, "Tempo para aguardar por filhos deve ser >= 0"

        filhos = []
        filtro = filtro or (lambda e: e.visivel)
        finder = self.uiaelement.FindAll(
            uiaclient.TreeScope_Children,
            ElementoUIA.UIA.CreateTrueCondition()
        )

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or (not filhos and cronometro < aguardar):
            primeiro = False

            for i in range(finder.Length):
                filho: uiaclient.IUIAutomationElement = finder.GetElement(i)
                e = ElementoUIA(filho.CurrentNativeWindowHandle, self.janela, self.profundidade + 1, filho)
                try:
                    if filtro(e): filhos.append(e)
                except Exception: pass

        return filhos

    def focar (self) -> typing.Self:
        if not self.janela.focada:
            self.janela.focar()
        try: self.uiaelement.SetFocus()
        except Exception: pass
        return self.aguardar()

    def clicar (self, botao: bot.tipagem.BOTOES_MOUSE = "left",
                      focar: bool = True) -> typing.Self:
        if focar: self.focar()
        invocavel = self.pattern.invocavel

        if invocavel is not None and botao == "left":
            try:
                invocavel.Invoke()
                return self.sleep(0.01).aguardar()
            except Exception: pass

        return super().clicar(botao, focar)

    def input (self, texto: str, focar: bool = True) -> typing.Self:
        if focar: self.focar()
        valor = self.pattern.valor

        if valor is not None:
            try:
                valor.SetValue(texto)
                return self.sleep(0.01).aguardar()
            except Exception: pass

        return super().input(texto, focar)

    def limpar (self) -> typing.Self:
        valor = self.pattern.valor
        if valor is not None:
            try:
                valor.SetValue(None)
                return self.sleep(0.01).aguardar()
            except Exception: pass

        return super().limpar()

    def selecionar (self, texto: str) -> None:
        """Selecionar a opção que possua o `texto`
        - Elemento deve ser `expansivel` e conter `item_selecionavel`"""
        texto = texto.lower()
        expansivel = self.pattern.expansivel
        assert expansivel, f"Elemento não é expansível {self}"

        self.focar()
        expansivel.Expand()
        self.aguardar()

        (
            self.encontrar(lambda e: texto in e.texto.lower() and
                                     e.pattern.item_selecionavel is not None)
            .pattern
            .item_selecionavel
            .Select() # type: ignore
        )

        expansivel.Collapse()
        self.aguardar()

    def abrir_abas (self, *nomes: str) -> ElementoUIA:
        """Abrir as abas `*nome` e retornar o elemento
        - Procurado por elementos `aba` e `item_aba`"""
        assert nomes, "Pelo menos 1 nome é necessário para abrir as abas do elemento"

        elemento = self
        for nome in nomes:
            aba = elemento.aguardar().encontrar(
                lambda e: nome in String(e.texto) and e.tipo.item_aba,
                aguardar = 1,
                msg_erro = f"Falha ao abrir as abas{nomes}. Aba {nome!r} não encontrada"
            )
            if s := aba.pattern.item_selecionavel: s.Select()
            else: aba.clicar()
            elemento = aba.parente

        if painel := elemento.filhos(lambda e: nomes[-1] in String(e.texto) and not e.tipo.item_aba):
            return painel[0]
        if not elemento.tipo.aba:
            raise Exception(f"Abas abertas {nomes} com sucesso, porém o elemento final não foi encontrado")
        return elemento

class JanelaW32:
    """Classe para manipulação de janelas e elementos para o backend Win32

    ### Criação
    ```
    JanelaW32.FromFoco()                                        # Janela focada
    JanelaW32("Título ou ClassName")                            # Procurar Janela visível
    JanelaW32(lambda j: "titulo" in j.titulo and j.visivel)     # Procurar a janela com filtro dinâmico
    JanelaW32(lambda j: ..., aguardar=10)                       # Aguardar por 10 segundos até encontrar a janela
    JanelaW32.Iniciar("notepad", shell=True, aguardar=30)       # Iniciar uma janela via novo processo
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
    janela.normal
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
    elemento.input("texto")     # Substituir o texto do elemento pelo `texto`
    ...
    # Acessores Janela/Elemento, visível e ativo, ordenando pela posição Y e X
    elemento[0]                 # Obter elemento via `index`
    elemento[0, -1]             # Obter elementos via `index`
    elemento ^  2               # Subir para o parente do elemento até uma determinada profundidade
    elemento << 2               # Subir para o parente do elemento n vezes
    janela / "OK"               # Obter elemento filho via `class_name` ou `texto`
    janela // "OK"              # Obter elemento descendente via `class_name` ou `texto`
    janela > "TPanel"           # Obter elementos filhos via `class_name` ou `texto`
    janela >> "TPanel"          # Obter elementos descendentes via `class_name` ou `texto`
    janela @ "JanelaInterna"    # Obter janela interna via `class_name` ou `texto`
    ```

    ### Métodos
    ```
    janela.maximizar()
    janela.restaurar()
    janela.minimizar()
    janela.focar()              # Trazer a janela para primeiro plano
    janela.aguardar()           # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
    janela.sleep()              # Aguardar por `segundos` até continuar a execução
    janela.janelas_processo()   # Janelas do mesmo processo da `janela`
    janela.print_arvore()       # Realizar o `print()` da árvore de elementos da janela e das janelas do processo
    ```

    ### Métodos acessores
    ```
    janela.to_uia()     # Obter uma instância da `JanelaW32` como `JanelaUIA`
    janela.dialogo()    # Encontrar janela de diálogo com `class_name`
    janela.popup()      # Encontrar janela de popup com `class_name`
    janela.tooltips()   # Obter os textos concatenados por `;` das `tooltips` (Caixa de texto com informação sobre o elemento)
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

    def __init__[T: JanelaW32] (self: T, filtro: str | typing.Callable[[T], bot.tipagem.SupportsBool],
                                         aguardar: int | float = 0,
                                         msg_erro: str | None = None) -> None:
        assert aguardar >= 0, "Tempo para aguardar por janela deve ser >= 0"

        if isinstance(filtro, str):
            nome = filtro
            msg_erro = msg_erro or f"Janela Nome={nome!r} não foi encontrada"
            filtro = lambda j: j.visivel and (
                j.class_name.lower() == nome.lower().strip()
                or nome in String(j.titulo)
            )

        encontrados = list[T]()
        def callback (hwnd: int, _) -> bool:
            j = self.FromHWND(hwnd)
            try:
                if filtro(j): encontrados.append(j) # type: ignore
            except Exception: pass
            return True

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or (not encontrados and cronometro < aguardar):
            primeiro = False
            try: win32gui.EnumWindows(callback, None)
            except Exception: pass

        match encontrados:
            case []: raise Exception(msg_erro or "Janela não encontrada para o filtro informado")
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
    def FromHWND[T: JanelaW32] (cls: type[T], hwnd: int) -> T:
        janela = object.__new__(cls)
        janela.hwnd = hwnd
        return janela

    @classmethod
    def FromFoco[T: JanelaW32] (cls: type[T]) -> T:
        """Obter a janela com o foco do sistema"""
        hwnd = win32gui.GetForegroundWindow()
        return cls.FromHWND(hwnd)

    @classmethod
    def Iniciar[T: JanelaW32] (cls: type[T], *argumentos: str, nome: str | None = None, shell: bool = True, aguardar: int | float = 30) -> T:
        """Iniciar uma janela no sistema a partir dos `argumentos`
        - `nome` para procurar pelo `titulo` ou `class_name`, se não primeira janela aberta
        - Alguns aplicativos podem abrir mais de uma janela, utilizar o `self.janelas_processo()` para verificar"""
        try:
            with cls.AguardarNovaJanela(nome, aguardar) as janela:
                bot.sistema.AbrirProcesso(*argumentos, shell=shell)
            return janela.focar()

        except Exception as erro:
            raise AssertionError(f"Falha ao iniciar uma janela com os argumentos '{" ".join(argumentos)}' | {erro}")

    @classmethod
    @contextlib.contextmanager
    def AguardarNovaJanela[T: JanelaW32] (cls: type[T], nome: str | None = None, aguardar: int | float = 15) -> typing.Generator[T, None, None]:
        """Aguardar e obter uma janela (visível) que irá abrir após executar alguma ação
        - `nome` para procurar pelo `titulo` ou `class_name`, se não primeira janela aberta
        - `Exception` caso não seja aberta nenhuma nova janela
        - Dentro do contexto apenas realizar a ação que abrirá a nova janela
        - Acessar a variável `as janela` apenas após o contexto

        #### Utilizar com o `with`
        ```
        with JanelaW32.AguardarNovaJanela(aguardar=2) as janela:
            bot.sistema.AbrirProcesso("notepad")
        print(janela.titulo)
        ```"""
        titulos = lambda: cls.titulos_janelas_visiveis()
        titulos_antes = titulos()
        janela = cls.FromHWND(0)
        yield janela

        try:
            nome = None if nome is None else nome.strip().lower()
            janela.hwnd = cls(
                lambda j:
                    j.titulo
                    and j.visivel
                    and j.titulo in titulos_antes.symmetric_difference(titulos())
                    and (
                        nome is None
                        or nome in j.class_name.lower()
                        or nome in j.titulo.lower()
                    ),
                aguardar = aguardar
            ).hwnd
        except Exception:
            raise Exception(f"Nenhuma nova janela foi encontrada após o tempo de espera") from None

    def __repr__ (self) -> str:
        return f"<{type(self).__name__} '{self.titulo}' class_name='{self.class_name}'>"

    def __eq__ (self, value: object) -> bool:
        return isinstance(value, type(self)) and self.elemento == value.elemento

    def __hash__ (self) -> int:
        return hash(self.hwnd)

    @functools.cached_property
    def elemento (self) -> ElementoW32:
        """Elemento superior da janela para acessar, procurar e manipular elementos"""
        return ElementoW32(self.hwnd, self)

    def __truediv__ (self, nome: str) -> ElementoW32:
        """Obter elemento filho visível e ativo
        - Possível de utilizar index no fim do nome `[0]`"""
        return self.elemento / nome

    def __floordiv__ (self, nome: str) -> ElementoW32:
        """Obter elemento descendente visível e ativo
        - Possível de utilizar index no fim do nome `[0]`"""
        return self.elemento // nome

    def __gt__ (self, nome: str) -> list[ElementoW32]:
        """Obter elementos filhos visível e ativo"""
        return self.elemento > nome

    def __rshift__ (self, nome: str) -> list[ElementoW32]:
        """Obter elementos descendentes visível e ativo"""
        return self.elemento >> nome

    def __matmul__ (self, nome: str) -> typing.Self:
        """Obter uma janela interna"""
        self.aguardar()
        janelas = list[typing.Self]()
        class_name = nome.strip().lower()

        def callback (hwnd: int, _) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True

            janela = self.FromHWND(hwnd)
            if janela.class_name.lower() == class_name or nome in String(janela.titulo):
                janelas.append(janela)

            return True

        try: win32gui.EnumChildWindows(self.hwnd, callback, None)
        except Exception: pass

        janelas = [janela
                   for janela in janelas
                   if janela.to_uia().elemento.pattern.window is not None]
        janelas = janelas or self.janelas_processo(
            lambda j: j.visivel and (
                j.class_name.lower() == class_name
                or nome in String(j.titulo)
            )
        )

        match janelas:
            case []: raise Exception(f"Janela Nome={nome!r} não foi encontrada")
            case [janela]: return janela
            # Ordenar pela quantidade filhos caso haja 2 ou mais
            case _: return sorted(
                janelas,
                key = lambda j: len(j.elemento.filhos())
            )[-1]

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
    def processo (self) -> psutil.Process:
        """Processo do módulo `psutil` para controle via `PID`"""
        _, pid = win32process.GetWindowThreadProcessId(self.hwnd)
        return psutil.Process(pid)

    @property
    def maximizada (self) -> bool:
        """Checar se a janela está em sua versão maximizada"""
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMAXIMIZED
    def maximizar (self) -> typing.Self:
        """Maximizar a janela e trazer para o foco"""
        win32gui.ShowWindow(self.hwnd, win32con.SW_MAXIMIZE)
        return self.aguardar().sleep(0.1)

    @property
    def normal (self) -> bool:
        """Checar se a janela está em sua versão normal
        - Nem maximizada e nem minimizada"""
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWNORMAL
    def restaurar (self) -> typing.Self:
        """Restaurar a janela e trazer para o foco
        - Caso estiver `minimizada`, é restaurada para o foco na sua versão anterior `maximizada/normal`
        - Caso estiver `maximizada`, é restaurada para o foco na sua versão `normal`
        - Caso estiver `normal`, apenas é feito o foco"""
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        return self.aguardar().sleep(0.1)

    @property
    def minimizada (self) -> bool:
        """Checar se a janela está em sua versão minimizada"""
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMINIMIZED
    def minimizar (self) -> typing.Self:
        """Minimizar a janela e remover o foco"""
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
            bot.tempo.aguardar(lambda: self.visivel, timeout=5, delay=0.5)

        flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        def trazer_para_o_foco () -> bool:
            try:
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
                win32gui.SetForegroundWindow(self.hwnd)
                return self.focada
            except Exception: return False
        focado = bot.tempo.aguardar(trazer_para_o_foco, timeout=5)

        # O Windows pode não permitir
        # Clicando em cima da janela resolve
        if not focado:
            bot.mouse.mover(self.coordenada.topo()).clicar()
            trazer_para_o_foco()

        return self.sleep(0.01).aguardar()

    @property
    def fechada (self) -> bool:
        return not win32gui.IsWindow(self.hwnd)
    def fechar (self, timeout: float | int = 10.0) -> bool:
        """Enviar a mensagem de fechar para janela e retornar indicador se fechou corretamente"""
        if not self.fechada:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        return bot.tempo.aguardar(lambda: self.fechada, timeout)
    def destruir (self, timeout: float | int = 10.0) -> bool:
        """Enviar a mensagem de destruir para janela e retornar indicador se fechou corretamente"""
        if not self.fechada:
            win32gui.PostMessage(self.hwnd, win32con.WM_DESTROY, 0, 0)
        if not self.fechada:
            win32gui.PostMessage(self.hwnd, win32con.WM_QUIT, 0, 0)
        return bot.tempo.aguardar(lambda: self.fechada, timeout)
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

    def janelas_processo[T: JanelaW32] (self: T, filtro: typing.Callable[[T], bot.tipagem.SupportsBool] | None = None,
                                                 aguardar: int | float = 0) -> list[T]:
        """Janelas do mesmo processo da `janela`
        - `filtro` para escolher as janelas. `Default: visível e ativo`
        - `aguardar` tempo em segundos para aguardar por alguma janela"""
        self.aguardar()
        encontrados: list[T] = []
        filtro = filtro or (lambda j: j.visivel and j.elemento.ativo)

        def callback (hwnd, _) -> typing.Literal[True]:
            if hwnd == self.hwnd: return True
            j = self.FromHWND(hwnd)

            try:
                if j.processo.pid == self.processo.pid and filtro(j):
                    encontrados.append(j)
            except Exception: pass
            return True

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or (not encontrados and cronometro < aguardar):
            primeiro = False
            try: win32gui.EnumWindows(callback, None)
            except Exception: pass

        return encontrados

    def dialogo (self, class_name: str = "#32770",
                       aguardar: int | float = 0) -> Dialogo | None:
        """Encontrar janela de diálogo com `class_name`
        - `None` caso não encontre
        - `aguardar` tempo em segundos para aguardar pelo diálogo"""
        assert aguardar >= 0, "Tempo para aguardar pelo diálogo deve ser >= 0"
        self.aguardar()

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or cronometro < aguardar:
            primeiro = False

            for janela in self.janelas_processo(lambda j: j.class_name == class_name and j.elemento.ativo):
                return Dialogo(janela.elemento)
            for filho in self.elemento.filhos(lambda e: e.class_name == class_name and e.ativo):
                return Dialogo(filho)

    def popup (self, class_name: str = "#32768",
                     aguardar: int | float = 0) -> Popup | None:
        """Encontrar janela de popup com `class_name`
        - `None` caso não encontre
        - `aguardar` tempo em segundos para aguardar pelo popup"""
        assert aguardar >= 0, "Tempo para aguardar pelo popup deve ser >= 0"
        self.aguardar()

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or cronometro < aguardar:
            primeiro = False

            for janela in self.janelas_processo(lambda j: j.class_name == class_name and j.elemento.ativo):
                return Popup(janela.elemento)
            for filho in self.elemento.filhos(lambda e: e.class_name == class_name and e.ativo):
                return Popup(filho)

    def tooltips (self, *class_name: str, aguardar: int = 5) -> str:
        """Obter os textos concatenados por `;` das `tooltips` (Caixa de texto com informação sobre o elemento)
        ### Útil em alguns para obter contexto quando realizar hover de mouse
        - `class_name` para informar demais `class_name` para serem procurados
        - `aguardar` tempo em segundos para aguardar por algum elemento"""
        assert aguardar >= 0, "Tempo para aguardar pelo popup deve ser >= 0"
        self.aguardar()

        elementos = list[ElementoUIA]()
        class_names = { "tooltip", "hint", *map(str.lower, class_name) }
        def classname_tooltip (elemento: ElementoUIA) -> bool:
            return (
                elemento.uiaelement.CurrentControlType == uiaclient.UIA_ToolTipControlTypeId
                or any(class_name in elemento.class_name.lower() for class_name in class_names)
            )

        primeiro, cronometro = True, bot.tempo.Cronometro()
        while primeiro or (not elementos and cronometro < aguardar):
            primeiro = False

            for janela in self.to_uia().janelas_processo(lambda _: True):
                elemento = janela.elemento
                if classname_tooltip(elemento):
                    elementos.append(elemento)
                    continue

                try: elementos.append(elemento.encontrar(lambda e: classname_tooltip(e)))
                except Exception: pass

        return "; ".join(elemento.texto for elemento in elementos)

    def capturar_dialogos (self, callback_tratamento: typing.Callable[[Dialogo], None] | None = None,
                                 aguardar: int | float = 0.5) -> None:
        """Realizar a captura de diálogo(s) na janela e aplicar o `callback_tratamento` para realizar alguma ação no diálogo
        - `AssertionError` caso algum diálogo continue aparecendo após o tratamento"""
        if callback_tratamento is not None:
            for _ in range(10):
                dialogo = self.aguardar().dialogo(aguardar=aguardar)
                if not dialogo: break

                texto = dialogo.texto
                callback_tratamento(dialogo)
                assert dialogo.aguardar_fechar(), f"Diálogo não fechou corretamente: '{texto}'"

        if dialogo := self.aguardar().dialogo(aguardar=aguardar):
            raise AssertionError(f"Diálogo inesperado: '{dialogo.texto}'")

    def print_arvore (self) -> None:
        """Realizar o `print()` da árvore de elementos da janela e das janelas do processo"""
        for janela in (self, *self.janelas_processo(lambda j: True)):
            janela.elemento.print_arvore()
            print()

    def to_uia (self) -> JanelaUIA:
        """Obter uma instância da `JanelaW32` como `JanelaUIA`"""
        return JanelaUIA.FromHWND(self.hwnd)

    @staticmethod
    def titulos_janelas_visiveis () -> set[str]:
        encontrados = set()
        def callback (hwnd: int, _) -> bool:
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
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
    JanelaUIA.FromFoco()                                    # Janela focada
    JanelaUIA("Título ou ClassName")                        # Procurar Janela visível
    JanelaUIA(lambda j: "titulo" in j.titulo and j.visivel) # Procurar a janela com filtro dinâmico
    JanelaUIA(lambda j: ..., aguardar=10)                   # Aguardar por 10 segundos até encontrar a janela
    JanelaUIA.Iniciar("notepad", shell=True, aguardar=30)   # Iniciar uma janela via novo processo
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
    janela.normal
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
    elemento.input("texto")     # Substituir o texto do elemento pelo `texto`
    ...
    # Acessores Janela/Elemento, visível e ativo, ordenando pela posição Y e X
    elemento[0]                 # Obter elemento via `index`
    elemento[0, -1]             # Obter elementos via `index`
    elemento ^  2               # Subir para o parente do elemento até uma determinada profundidade
    elemento << 2               # Subir para o parente do elemento n vezes
    janela / "OK"               # Obter elemento filho via `class_name` ou `texto`
    janela // "OK"              # Obter elemento descendente via `class_name` ou `texto`
    janela > "TPanel"           # Obter elementos filhos via `class_name` ou `texto`
    janela >> "TPanel"          # Obter elementos descendentes via `class_name` ou `texto`
    janela @ "JanelaInterna"    # Obter janela interna via `class_name` ou `texto`
    ```

    # Específico UIA
    elemento.valor              # Propriedade `value` do elemento. Útil para inputs
    elemento.automation_id      # Checar se o elemento é uma aba
    elemento.tipo
    elemento.pattern
    ...
    ```

    ### Métodos
    ```
    janela.maximizar()
    janela.restaurar()
    janela.minimizar()
    janela.focar()              # Trazer a janela para primeiro plano
    janela.aguardar()           # Aguarda `timeout` segundos até que a thread da GUI fique ociosa
    janela.sleep()              # Aguardar por `segundos` até continuar a execução
    janela.janelas_processo()   # Janelas do mesmo processo da `janela`
    janela.print_arvore()       # Realizar o `print()` da árvore de elementos da janela e das janelas do processo

    # Específico UIA
    janela.menu("Arquivo", "Salvar") # Selecionar as `opções` nos menus
    ```

    ### Métodos acessores
    ```
    janela.dialogo()    # Encontrar janela de diálogo com `class_name`
    janela.popup()      # Encontrar janela de popup com `class_name`
    janela.tooltips()   # Obter os textos concatenados por `;` das `tooltips` (Caixa de texto com informação sobre o elemento)
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

    def __truediv__ (self, nome: str) -> ElementoUIA:
        return self.elemento / nome

    def __floordiv__ (self, nome: str) -> ElementoUIA:
        return self.elemento // nome

    def __gt__ (self, nome: str) -> list[ElementoUIA]: # type: ignore
        return self.elemento > nome

    def __rshift__ (self, nome: str) -> list[ElementoUIA]: # type: ignore
        return self.elemento >> nome

    @property
    def maximizada (self) -> bool:
        pattern = self.elemento.pattern.window
        if not pattern: return False
        return pattern.CurrentWindowVisualState == uiaclient.WindowVisualState_Maximized
    def maximizar (self) -> typing.Self:
        pattern = self.elemento.pattern.window
        if pattern: pattern.SetWindowVisualState(uiaclient.WindowVisualState_Maximized)
        else: super().maximizar()
        return self

    @property
    def normal (self) -> bool:
        pattern = self.elemento.pattern.window
        if not pattern: return not self.minimizada and not self.maximizada
        return pattern.CurrentWindowVisualState == uiaclient.WindowVisualState_Normal
    def restaurar (self) -> typing.Self:
        """Restaurar a janela e trazer para o foco
        - Caso estiver `minimizada/maximizada`, é restaurada para o foco na sua versão `normal`
        - Caso estiver `normal`, apenas é feito o foco"""
        pattern = self.elemento.pattern.window
        if pattern: pattern.SetWindowVisualState(uiaclient.WindowVisualState_Normal)
        else: super().restaurar()
        return self

    @property
    def minimizada (self) -> bool:
        pattern = self.elemento.pattern.window
        if not pattern: return not self.fechada
        return pattern.CurrentWindowVisualState == uiaclient.WindowVisualState_Minimized
    def minimizar (self) -> typing.Self:
        pattern = self.elemento.pattern.window
        if pattern: pattern.SetWindowVisualState(uiaclient.WindowVisualState_Minimized)
        else: super().minimizar()
        return self

    def menu (self, *opcoes: str) -> typing.Self:
        """Selecionar as `opções` nos menus
        - Procurado por elementos `barra_menu` com `item_barra_menu`"""
        self.focar()
        barras_menu_usadas = set[ElementoUIA]()

        def barras_menu_nao_usadas () -> list[ElementoUIA]:
            """Procurar barras de menu nos descendentes e janelas do processo"""
            elementos = self.elemento.descendentes(
                lambda e: e not in barras_menu_usadas and e.tipo.barra_menu,
                aguardar = 1
            )
            elementos.extend(
                janela.elemento
                for janela in self.janelas_processo(
                    lambda j: j.elemento not in barras_menu_usadas and j.elemento.tipo.barra_menu
                )
            )
            return elementos

        # mover o mouse para o topo para não interferir
        bot.mouse.mover(self.coordenada.topo())

        for opcao in map(str.lower, opcoes):
            opcao_encontrada = False
            self.sleep(0.1).aguardar()

            for barra_menu in barras_menu_nao_usadas():
                barras_menu_usadas.add(barra_menu)
                finder = barra_menu.uiaelement.FindAll(
                    # SubTree pega todos os itens da barra que o Children não consegue
                    uiaclient.TreeScope_Subtree,
                    ElementoUIA.UIA.CreateTrueCondition()
                )

                for i in range(finder.Length):
                    filho: uiaclient.IUIAutomationElement = finder.GetElement(i)
                    e = ElementoUIA(filho.CurrentNativeWindowHandle, self, barra_menu.profundidade + 1, filho)
                    if opcao != e.texto.lower() or not e.tipo.item_barra_menu:
                        continue

                    pattern = e.pattern
                    if (expansivel := pattern.expansivel)\
                        and expansivel.Expand() != -1\
                        and expansivel.CurrentExpandCollapseState > 0: pass
                    elif invocavel := pattern.invocavel: invocavel.Invoke()
                    else: e.clicar(focar=False)

                    opcao_encontrada = True
                    break

                if opcao_encontrada:
                    break

            assert opcao_encontrada, f"Opção '{opcao}' não encontrada nas barras de menu"

        return self.sleep(0.1).aguardar()

__all__ = [
    "JanelaUIA",
    "JanelaW32",
]