@echo off
echo Criando ambiente virtual com uv
pip install uv
uv venv
call .venv\Scripts\activate.bat
uv sync

echo.
echo Instalando o pacote em modo desenvolvimento com dependencias extras
uv pip install -e .
uv pip install ".[ocr]"

echo.
echo Empacotando
uv build --wheel