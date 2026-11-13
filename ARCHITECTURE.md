# JetUML Python — Arquitetura de Software

## 1. Visão Geral
O sistema adota uma arquitetura em camadas desacopladas orientada a eventos e comandos:

- `jetuml.core`: Grafo de elementos, nós, arestas, validações estritas, command stack (undo/redo), área de transferência e persistência.
- `jetuml.export`: Exportação pura para SVG e rasterização para PNG/JPEG via Pillow.
- `jetuml.view`: Interface Tkinter modular, abas, ferramentas, canvas interativo com suporte a zoom, snap-to-grid, notificações e diálogos modais.
