"""Extraccion de datos de etiqueta desde un PDF de Odoo."""

import re

import fitz  # PyMuPDF

# Una linea de 12 a 14 digitos puros se considera codigo de barras.
_BARCODE_RE = re.compile(r"^\d+$")
# Una linea que es solo "(...)" se considera referencia interna y se ignora.
_REF_RE = re.compile(r"^\([^()]*\)$")
# Codigo de referencia interna tipo "855-2/55029".
_INTERNAL_REF_RE = re.compile(r"^\d+-\d+/\d+$")
# Referencia sola, sin espacios y abierta con parentesis o corchete, tipo
# "(658488/202039E/2020" (Odoo la corta sin cerrar).
_OPEN_REF_RE = re.compile(r"^[\[(][^\s]*$")
# Prefijo "[referencia]" con el que Odoo encabeza el nombre del producto.
_REF_PREFIX_RE = re.compile(r"^\[[^\]]*\]\s*")


def extract_labels(pdf_path):
    """Extrae los datos de etiqueta de cada pagina de un PDF.

    Args:
        pdf_path: ruta al archivo PDF.

    Returns:
        Lista de dicts con claves 'barcode', 'name' y 'price', una por pagina.
    """
    labels = []
    doc = fitz.open(pdf_path)
    try:
        if not len(doc):
            raise ValueError("El PDF no contiene paginas.")
        for page in doc:
            for cell in _cells(page):
                label = _parse_page(page.get_text(clip=cell))
                if not label["barcode"] and not label["name"]:
                    continue  # recuadro vacio de la hoja
                labels.append(label)
    finally:
        doc.close()

    if not labels:
        raise ValueError("El PDF no contiene etiquetas legibles.")

    print(f"PDF leido: {len(labels)} etiqueta(s)")
    return labels


def _cells(page):
    """Ubica los recuadros de etiqueta dibujados en una pagina.

    Junta los trazos que se tocan: cada etiqueta de Odoo dibuja su marco con
    varios rectangulos finos, asi que cada grupo resultante es una etiqueta.

    Args:
        page: pagina de PyMuPDF.

    Returns:
        Lista de fitz.Rect en orden de lectura. Si la pagina no tiene recuadros
        (formato de una etiqueta por pagina), devuelve la pagina entera.
    """
    boxes = []
    for drawing in page.get_drawings():
        rect = fitz.Rect(drawing["rect"])
        if rect.is_empty:
            continue
        for box in [b for b in boxes if fitz.Rect(b) + (-1, -1, 1, 1) & rect]:
            boxes.remove(box)
            rect = rect | box
        boxes.append(rect)

    cells = [b for b in boxes if b.width > 50 and b.height > 30]
    if not cells:
        return [page.rect]
    return sorted(cells, key=lambda r: (round(r.y0), round(r.x0)))


def _parse_page(text):
    """Separa el texto de una pagina en codigo de barras, nombre y precio."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    barcode = ""
    price = ""
    name_parts = []

    for line in lines:
        if not barcode and _BARCODE_RE.match(line):
            barcode = line
        elif not price and "$" in line:
            price = line
        elif (
            _REF_RE.match(line)
            or _INTERNAL_REF_RE.match(line)
            or _OPEN_REF_RE.match(line)
        ):
            continue  # referencia interna del producto
        else:
            name_parts.append(_REF_PREFIX_RE.sub("", line))

    return {
        "barcode": barcode,
        "name": " ".join(name_parts),
        "price": price,
    }
