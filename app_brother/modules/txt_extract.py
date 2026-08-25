"""Extraccion de datos de etiqueta desde un TXT con bloques ZPL de Odoo."""

import re

# Cada etiqueta ZPL esta delimitada por ^XA ... ^XZ.
_BLOCK_RE = re.compile(r'\^XA(.*?)\^XZ', re.DOTALL)

# Texto de fuente grande (altura >= 35): es el nombre del producto.
_NAME_RE = re.compile(r'\^A0N,(\d+),\d+\^FD(.*?)\^FS')

# Barcode: digitos que siguen a un comando ^BC.
_BARCODE_RE = re.compile(r'\^BC.*?\^FD(\d+)\^FS', re.DOTALL)

# Precio: campo que contiene "$" o simbolo monetario.
_PRICE_RE = re.compile(r'\^FD([^F]*\$[^F]*)\^FS')

# Prefijo "[referencia]" con el que Odoo encabeza el nombre del producto.
_REF_PREFIX_RE = re.compile(r'^\[[^\]]*\]\s*')


def extract_labels(txt_path):
    """Extrae los datos de etiqueta de un archivo TXT con bloques ZPL.

    Args:
        txt_path: ruta al archivo TXT generado por Odoo.

    Returns:
        Lista de dicts con claves 'barcode', 'name' y 'price', una por bloque.

    Raises:
        ValueError: si el archivo no contiene bloques ZPL legibles.
    """
    with open(txt_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    labels = []
    for match in _BLOCK_RE.finditer(content):
        label = _parse_block(match.group(1))
        if label["barcode"] or label["name"]:
            labels.append(label)

    if not labels:
        raise ValueError("No se encontraron etiquetas ZPL en el archivo.")

    print(f"TXT leido: {len(labels)} etiqueta(s)")
    return labels


def _parse_block(block):
    """Extrae barcode, nombre y precio de un bloque ^XA...^XZ."""
    barcode = ""
    barcode_match = _BARCODE_RE.search(block)
    if barcode_match:
        barcode = barcode_match.group(1)

    name = ""
    for match in _NAME_RE.finditer(block):
        if int(match.group(1)) >= 35:
            name = _REF_PREFIX_RE.sub("", match.group(2)).strip()
            break

    price = ""
    price_match = _PRICE_RE.search(block)
    if price_match:
        price = price_match.group(1).strip()

    return {"barcode": barcode, "name": name, "price": price}
