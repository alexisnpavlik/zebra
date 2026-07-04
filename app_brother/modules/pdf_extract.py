"""Extraccion de datos de etiqueta desde un PDF de Odoo."""

import re

import fitz  # PyMuPDF

# Una linea de 12 a 14 digitos puros se considera codigo de barras.
_BARCODE_RE = re.compile(r"^\d+$")
# Una linea que es solo "(...)" se considera referencia interna y se ignora.
_REF_RE = re.compile(r"^\([^()]*\)$")
# Codigo de referencia interna tipo "855-2/55029".
_INTERNAL_REF_RE = re.compile(r"^\d+-\d+/\d+$")


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
        for page in doc:
            labels.append(_parse_page(page.get_text()))
    finally:
        doc.close()

    if not labels:
        raise ValueError("El PDF no contiene paginas.")

    print(f"PDF leido: {len(labels)} etiqueta(s)")
    return labels


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
        elif _REF_RE.match(line) or _INTERNAL_REF_RE.match(line):
            continue  # referencia interna del producto
        else:
            name_parts.append(line)

    return {
        "barcode": barcode,
        "name": " ".join(name_parts),
        "price": price,
    }
