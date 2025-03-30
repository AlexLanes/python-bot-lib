@echo off
echo Criando ambiente virtual com uv
uv venv

echo.
echo Ativando ambiente
call .venv\Scripts\activate.bat

echo.
echo Instalando pacotes necessários (wheel, build)
uv pip install wheel build

echo.
echo Instalando o pacote em modo desenvolvimento
uv pip install -e .

echo.
echo Instalando dependencias extras
uv pip install ".[ocr]"

echo Limpando arquivos de build
rmdir /s /q build
rmdir /s /q bot.egg-info

echo.
echo Gerando lockfile com uv
uv pip compile pyproject.toml --output-file=uv.lock

echo.
echo Empacotando
python -m build --wheel