from setuptools import setup, find_packages

setup(
    name="bot",
    version="1.6.2",
    packages=find_packages(),
    author="Alex Lanes Angelo",
    author_email="alex_lanes@hotmail.com",
    description="Pacote com funcionalidades gerais para criação de Bots",
    url="https://github.com/AlexLanes/python-bot-lib",
    python_requires=">=3.12",
    include_package_data=True,
    install_requires=[
        linha.strip()
        for linha in open("./requirements.txt", "r", encoding="utf-8").readlines()
        if not linha.isspace() and not linha.startswith("#")
    ],
    package_data={
        "bot": ["windows/QRes.exe"],
    },
    extras_require={
        "ocr": ["easyocr"],
    },
)
