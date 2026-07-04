# Graph Report - zebra_label_printer_odoo  (2026-07-04)

## Corpus Check
- 22 files · ~53,131 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 157 nodes · 195 edges · 17 communities (13 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `91c89818`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `BrotherLabelPrinterApp` - 16 edges
2. `LabelPrinterApp` - 11 edges
3. `clean_text()` - 6 edges
4. `Diseño: Toggle para imprimir número de código de barras` - 6 edges
5. `build_label()` - 5 edges
6. `normalize_price()` - 5 edges
7. `truncate_name()` - 5 edges
8. `build_label()` - 5 edges
9. `app_zebra — cadena de parámetros` - 5 edges
10. `app_brother — manipulación de PDF` - 5 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `BrotherLabelPrinterApp`  [EXTRACTED]
  app_brother/main.py → app_brother/modules/gui.py
- `main()` --calls--> `LabelPrinterApp`  [EXTRACTED]
  app_zebra/main.py → app_zebra/modules/gui.py
- `_barcode()` --calls--> `clean_text()`  [EXTRACTED]
  app_zebra/modules/zpl_label.py → app_zebra/modules/label_text.py
- `_price()` --calls--> `normalize_price()`  [EXTRACTED]
  app_zebra/modules/zpl_label.py → app_zebra/modules/label_text.py
- `_name()` --calls--> `truncate_name()`  [EXTRACTED]
  app_zebra/modules/zpl_label.py → app_zebra/modules/label_text.py

## Import Cycles
- None detected.

## Communities (17 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (14): main(), Punto de entrada del impresor de etiquetas Brother QL-800., _display_name(), Interfaz gráfica para imprimir etiquetas en la impresora Brother QL-800., Texto que se muestra en el desplegable para una impresora., Ventana principal del impresor de etiquetas Brother QL-800., BrotherLabelPrinterApp, Detecta las impresoras del sistema y llena el desplegable. (+6 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (12): main(), Punto de entrada del impresor de etiquetas Zebra., _display_name(), Interfaz grafica para imprimir etiquetas desde un PDF., Texto que se muestra en el desplegable para una impresora., Ventana principal del impresor de etiquetas., LabelPrinterApp, Detecta las impresoras de CUPS y llena el desplegable. (+4 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (21): _barcode(), build_label(), _centered_x(), _name(), _price(), Generacion de etiquetas en lenguaje EPL (Zebra GC420t y similares)., Comandos EPL que abren una fila de etiquetas., Comando EPL que imprime la fila. (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (14): app_brother — manipulación de PDF, app_zebra — cadena de parámetros, Diseño: Toggle para imprimir número de código de barras, `epl_label.py`, GUI (ambas apps), `gui.py`, `gui.py` — `_build_widgets`, `gui.py` — `_load_settings` / `_save_settings` (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.22
Nodes (12): _barcode(), build_label(), _centered_text(), _name(), _price(), Generacion de etiquetas en lenguaje ZPL (Zebra ZD421 y similares)., Comandos ZPL que abren una fila de etiquetas., Comando ZPL que cierra e imprime la fila. (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.26
Nodes (11): list_printers(), _list_printers_cups(), _list_printers_windows(), Deteccion de impresoras y envio de trabajos crudos (Windows y Linux/Mac)., infer_language(), Deduce el lenguaje EPL o ZPL a partir del nombre de la cola., Lista las impresoras disponibles en el sistema.      Returns:         Lista de d, Envia un flujo crudo (EPL o ZPL) a la impresora indicada.      Args:         raw (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.29
Nodes (9): list_printers(), _list_printers_cups(), _list_printers_windows(), Módulo de detección de impresoras e impresión nativa de PDFs (Brother y estándar, print_pdf(), _print_pdf_cups(), _print_pdf_windows(), Lista todas las impresoras disponibles en el sistema.      Returns:         List (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.40
Nodes (5): extract_labels(), _parse_page(), Extraccion de datos de etiqueta desde un PDF de Odoo., Extrae los datos de etiqueta de cada pagina de un PDF.      Args:         pdf_pa, Separa el texto de una pagina en codigo de barras, nombre y precio.

### Community 8 - "Community 8"
Cohesion: 0.40
Nodes (5): extract_labels(), _parse_page(), Extraccion de datos de etiqueta desde un PDF de Odoo., Extrae los datos de etiqueta de cada pagina de un PDF.      Args:         pdf_pa, Separa el texto de una pagina en codigo de barras, nombre y precio.

### Community 9 - "Community 9"
Cohesion: 0.40
Nodes (5): extract_labels(), _parse_block(), Extraccion de datos de etiqueta desde un TXT con bloques ZPL de Odoo., Extrae los datos de etiqueta de un archivo TXT con bloques ZPL.      Args:, Extrae barcode, nombre y precio de un bloque ^XA...^XZ.

## Knowledge Gaps
- **12 isolated node(s):** `Uso`, `Resumen`, `GUI (ambas apps)`, ``gui.py``, ``label_layout.py`` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Empaqueta la app de Brother en un ejecutable standalone con PyInstaller.  Uso:`, `Punto de entrada del impresor de etiquetas Brother QL-800.`, `Interfaz gráfica para imprimir etiquetas en la impresora Brother QL-800.` to the rest of the system?**
  _65 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09852216748768473 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.1225296442687747 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._