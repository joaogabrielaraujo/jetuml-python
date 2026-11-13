# JetUML em Python

Editor de diagramas UML desktop desenvolvido do zero em Python com Tkinter, seguindo os princípios de SOLID, Clean Code e padrões de projeto orientados a objetos.

## Instalação e Execução

### Requisitos
- Python 3.10 ou superior
- Pillow (para exportação PNG/JPEG)
- pytest (para execução dos testes)

```bash
pip install -r requirements.txt
python -m jetuml
```

## Formato de Arquivo Aberto (RNF02)
Os diagramas são salvos em formato `.json` com estrutura declarativa aberta.

## Testes Automatizados
```bash
pytest tests/
# ou
python -m unittest discover tests
```
