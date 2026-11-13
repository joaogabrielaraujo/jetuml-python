# Resposta 02

**Data/Hora:** 2026-10-15 14:43

## Conteúdo da Resposta

Atendendo estritamente ao requisito do projeto, **nenhum código-fonte do JetUML original foi consultado**. A análise a seguir foi realizada 100% com base no código-fonte deste repositório (`jetuml_python`), em sua arquitetura interna, nos requisitos referenciados nas docstrings (`RF01-RF42`, `RNF02`) e nas especificações e boas práticas da notação UML.

---

### 1. Por que o código não atualiza os métodos e atributos da classe?

A ausência dos atributos e métodos na interface após a edição ocorre por **quatro falhas encadeadas** no código:

#### Causa 1: O Canvas simplesmente não desenha os compartimentos de atributos e métodos (Falha Crítica)
Em `jetuml/view/canvas.py:L90-L93`, no método `redraw()`, o trecho que desenha a `ClassNode` é:

```python
if isinstance(node, ClassNode):
    self.create_rectangle(x, y, x + w, y + h, fill=theme.node_fill, outline=theme.node_stroke, width=1.5)
    self.create_text(x + w / 2, y + 14 * self.scale, text=node.name, font=("Segoe UI", int(10 * self.scale), "bold"), fill=theme.text_color)
    self.create_line(x, y + 26 * self.scale, x + w, y + 26 * self.scale, fill=theme.node_stroke)
```

> **O Canvas ignora completamente `node.attributes` e `node.methods`.**
> Ele desenha apenas o retângulo externo, o nome da classe e a primeira linha horizontal divisória. Não há qualquer instrução `create_text` para as linhas de atributos, nenhuma segunda linha divisória e nenhum `create_text` para os métodos. Mesmo que os dados existam no objeto, eles nunca são renderizados na tela do usuário.

---

#### Causa 2: As dimensões da classe (`_update_bounds`) não são recalculadas após a edição
No arquivo `jetuml/core/node.py:L98-L111`, o método `_update_bounds()` calcula o tamanho mínimo de altura e largura baseado no número de linhas e no tamanho do texto dos atributos e métodos.

No entanto, `_update_bounds()` só é invocado no `__init__`. Como `attributes` e `methods` são atributos simples (não properties com setters), ao alterar seus valores o nó **não recalcula sua altura nem sua largura**.

---

#### Causa 3: A janela de propriedades ignora o comando de Undo/Redo e o recálculo
No arquivo `jetuml/core/commands.py:L189-L218`, existe uma classe pronta chamada `EditPropertiesCommand` que executa `_update_bounds()` e permite desfazer/refazer com Ctrl+Z/Ctrl+Y:

```python
# Em commands.py (implementado mas não utilizado pela UI):
if hasattr(self.element, "_update_bounds"):
    getattr(self.element, "_update_bounds")()
self.diagram.notify_change()
```

Porém, em `jetuml/view/app.py:L263-L266`, o diálogo salva as alterações usando `setattr` bruto:

```python
PropertiesDialog(self.root, element, on_save=lambda p: (
    [setattr(element, k, v) for k, v in p.items()],
    active["diagram"].notify_change()
))
```
Isso faz com que:
1. `_update_bounds()` **não** seja chamado.
2. A alteração **não** entre na pilha de Undo/Redo (`active["stack"]`).

---

#### Causa 4: Exportação Raster e Área de Transferência também omitem os membros
Em `jetuml/export/raster_exporter.py:L44-L54` (utilizado para salvar em PNG/JPEG e copiar a imagem com Ctrl+B), o exportador desenha apenas um retângulo branco com o nome da classe:
```python
draw.rectangle([x, y, x + w_n, y + h_n], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
if hasattr(node, "name"):
    draw.text((x + 10, y + 8), getattr(node, "name"), fill=(0, 0, 0), font=font_bold)
```
O único lugar de todo o projeto onde o desenho de atributos e métodos chegou a ser implementado foi em `jetuml/export/svg_exporter.py:L100-L109`.

---

### 2. O que faz este código ser diferente do JetUML original / esperado?

Comparando a implementação deste repositório com as características e capacidades esperadas de uma ferramenta UML completa como o JetUML:

#### A. Arquitetura e Framework de Interface (Tkinter vs JavaFX/Swing)
- **Framework Gráfico:** O JetUML original é uma aplicação de desktop em **Java**, que utiliza **JavaFX** (anteriormente Swing) com renderização baseada em Scene Graph e aceleração gráfica. Este projeto foi reescrito em **Python** utilizando **Tkinter** com um `tk.Canvas` estático e redesenho manual via `delete("all")`.
- **Renderização e Redesenho:** No `canvas.py`, qualquer alteração ou arrasto de mouse dispara `self.redraw()`, que apaga todos os elementos da tela e os recria do zero, o que não escala bem para diagramas médios ou grandes.

#### B. Notação Gráfica UML Incompleta na Tela de Trabalho
- **Ausência de Marcadores nas Arestas (Herança, Composição, Agregação, etc.):**
  Em `jetuml/view/canvas.py:L72-L82`, todas as arestas são desenhadas como **linhas simples e sem pontas**. Na tela do usuário:
  - Não há triângulos vazios para *Generalização/Herança*;
  - Não há losangos brancos para *Agregação* nem pretos para *Composição*;
  - Não há setas abertas para *Dependência* ou *Navegabilidade*;
  - Não há rótulos de multiplicidade/cardinalidade visíveis nas pontas (`start_label`, `end_label`).
- **Renderização de Outros Nós no Canvas:**
  - `InterfaceNode`: cai no bloco `else:` genérico, não exibindo o estereótipo `«interface»` nem seus métodos.
  - `PackageNode`, `ObjectNode`, `FieldNode`, `ImplicitParameterNode` (linhas de vida de Sequência): todos caem no `else:` genérico e aparecem como meros retângulos com texto no centro.

#### C. Ferramentas da Toolbar desconectadas do Canvas
No arquivo `jetuml/view/toolbar.py`, foram declaradas dezenas de ferramentas para os 5 diagramas (Classe, Sequência, Estado, Objeto, Caso de Uso).
No entanto, no Canvas `jetuml/view/canvas.py:L122-L138`:
- O evento de clique (`on_mouse_down`) só reconhece 4 ferramentas de nós: `"Class"`, `"Note"`, `"State"` e `"Use Case"`.
- Clicar com ferramentas como **Interface, Package, Actor, Initial State, Final State, Object, Field, Implicit Parameter ou Call** não cria nenhum nó; ao invés disso, ativa o comportamento de criar aresta (*rubber-band*).
- O mesmo acontece na soltura do mouse (`on_mouse_up`): arestas como `Reference`, `Collaboration`, `CallEdge`, `ReturnEdge`, `Include` e `Extend` não são instanciadas.

#### D. Experiência de Edição (Diálogo Modal Forçado vs Edição Ágil)
- No JetUML original, a proposta principal é ser uma ferramenta de **esboço rápido (sketching)** com baixa fricção.
- Nesta versão em Python:
  - Não há edição de texto direta no Canvas (in-place text editing).
  - Toda edição depende de uma janela modal secundária (`PropertiesDialog`).
  - Ao criar qualquer elemento com `auto_edit_node` ativado, a janela modal trava a tela imediatamente.

#### E. Roteamento de Arestas e Autoarestas (Self-edges)
- No JetUML, arestas suportam roteamento ortogonal/manhattan e autoarestas (quando um nó aponta para si mesmo em transições ou associações reflexivas).
- Nesta versão:
  - Todas as arestas ligam apenas `s.connection_point` até `e.connection_point` em linha reta direta.
  - Conectar um nó a ele mesmo gera colapso de pontos no mesmo local (comprimento 0) e nada visível é desenhado.

#### F. Formatação de Notação UML não Integrada (Código Morto)
- Foi criado o módulo `jetuml/view/text_formatter.py` para interpretar marcações como `/abstrato/` (itálico) e `_estático_` (sublinhado).
- Contudo, **ele não é importado em nenhum outro arquivo**. As convenções de formatação não são aplicadas no Canvas nem nos exportadores.

#### G. Formato de Arquivo Proprietário
- O JetUML tradicionalmente trabalha com formatos próprios baseados na especificação do projeto (`.jet` ou esquemas XML/JSON completos).
- Esta versão salva em um formato simplificado em `.json` via `DiagramSerializer`, sem suporte à leitura de arquivos `.jet` legados.

---

### Resumo das Ações Necessárias para Corrigir a Atualização da Classe:

1. **Em `jetuml/view/canvas.py`:** Atualizar o bloco de desenho de `ClassNode` para iterar e desenhar as linhas de `node.attributes.splitlines()`, desenhar a segunda linha horizontal divisória e desenhar as linhas de `node.methods.splitlines()`.
2. **Em `jetuml/view/app.py`:** No callback do `PropertiesDialog`, substituir a atribuição direta por `EditPropertiesCommand`, garantindo a execução de `_update_bounds()` e o suporte a Undo/Redo.
3. **Em `jetuml/export/raster_exporter.py`:** Incluir a renderização dos compartimentos de atributos e métodos para que a exportação PNG/JPEG e a cópia para a área de transferência reflitam as alterações.
