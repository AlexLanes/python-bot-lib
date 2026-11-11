"""Pacote para realizar ações no sistema operacional
### `sistema.Caminho`
Classe para representação de caminhos do sistema operacional e manipulação de arquivos/diretórios

### Manipulação de Janelas
- `sistema.JanelaW32` api de backend `win32`
- `sistema.JanelaUIA` api de backend `uia`
- Combinar com script `uv run inspect` para visualizar a raiz de elementos

### Inicialização e encerramento de Processos
- `sistema.executar`
- `sistema.AbrirProcesso`
- `sistema.encerrar_processos_usuario`

### Clipboard
- `sistema.copiar_texto(texto: str)`
- `sistema.texto_copiado() -> str`

### sistema.Resolucao
Obter informações e realizar modificações da resolução da tela
"""

from bot.sistema.caminho import *
from bot.sistema.processo import *
from bot.sistema.setup import *
from bot.sistema.janela import *