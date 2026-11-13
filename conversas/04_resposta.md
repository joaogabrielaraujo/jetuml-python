# Resposta 04

**Data/Hora:** 2026-10-15 15:00

## Conteúdo da Resposta

As correções escaláveis foram aplicadas em todas as camadas arquiteturais do sistema (`core`, `view` e `export`), garantindo que métodos e atributos de classes (e de outros nós como interfaces e notas) sejam perfeitamente atualizados, dimensionados e renderizados, com suporte a Undo/Redo e renderização de marcadores UML.

---

### Resumo das Modificações Escaláveis Aplicadas

1. **Camada de Domínio (`jetuml/core/node.py`):**
   - **Properties Reativas:** `ClassNode.name`, `ClassNode.attributes` e `ClassNode.methods` foram convertidos em properties com setters dedicados que disparam automaticamente `_update_bounds()`. Qualquer modificação direta ou via diálogo recalcula a geometria da classe em tempo real.
   - **Cálculo Preciso de Limites:** O método `_update_bounds()` agora calcula a altura somando o cabeçalho (28px), o compartimento de atributos com base no número de linhas e o compartimento de métodos, garantindo proporção e tamanho mínimos adequados.
   - **Extensão a Outros Nós:** Aplicado o mesmo padrão a `InterfaceNode` (com estereótipo `«interface»` e métodos) e `NoteNode` (linhas de texto).

2. **Camada de Controle e Comandos (`jetuml/view/app.py`):**
   - **Adoção do Padrão Command:** Em `_open_props_dialog`, a atribuição imperativa direta foi substituída por `EditPropertiesCommand`.
   - **Suporte a Desfazer/Refazer (Undo/Redo):** Cada edição de nome, atributos ou métodos é enviada para a pilha de comandos (`active["stack"].execute(cmd)`), permitindo desfazer com **Ctrl+Z** e refazer com **Ctrl+Y**.

3. **Camada de Apresentação e Canvas (`jetuml/view/canvas.py`):**
   - **Renderização dos 3 Compartimentos de Classe:**
     - Compartimento 1: Nome da classe em negrito e linha divisória horizontal.
     - Compartimento 2: Linhas de atributos alinhadas à esquerda (`anchor="w"`) com padding e espaçamento escalável por zoom, seguidas da segunda linha divisória horizontal.
     - Compartimento 3: Linhas de métodos alinhadas à esquerda com padding escalável.
   - **Renderizadores Dedicados:** Modularização de `_draw_node` em funções especialistas por tipo (`_draw_class_node`, `_draw_interface_node`, `_draw_package_node`, `_draw_note_node`, `_draw_actor_node`, `_draw_use_case_node`, etc.).
   - **Marcadores de Relação UML no Canvas:** Implementação de pontas de flechas e marcadores em `_draw_edge`:
     - Triângulo vazado para Herança e Realização.
     - Losango vazado para Agregação e preenchido para Composição.
     - Seta aberta para Dependência e direcionamento.
     - Rótulos de texto e multiplicidades (`middle_label`, `start_label`, `end_label`).
   - **Fábricas de Ferramentas Desacopladas:** Tabelas de despacho `NODE_TOOL_FACTORIES` e `EDGE_TOOL_FACTORIES` que conectam todas as ferramentas da barra lateral à criação direta no Canvas.

4. **Camada de Exportação Raster (`jetuml/export/raster_exporter.py`):**
   - Atualizado o exportador Pillow para renderizar os 3 compartimentos de `ClassNode` e `InterfaceNode` em exportações PNG/JPEG e na cópia de imagem para a área de transferência (`Ctrl+B`).

5. **Testes Automatizados (`tests/test_class_node_properties.py`):**
   - Teste de recálculo dinâmico de limites em `ClassNode`.
   - Teste de Undo e Redo com `EditPropertiesCommand`.
   - Teste de recálculo de limites em `InterfaceNode`.
   - Teste de exportação SVG e Raster contendo atributos e métodos.
   - Teste de carregamento do diagrama de exemplo (`examples/class_diagram.json`).
   - Todos os 9 testes do projeto passaram com 100% de sucesso.
