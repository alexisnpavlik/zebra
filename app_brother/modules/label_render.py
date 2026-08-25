"""Dibujo de la etiqueta Brother en PDF a partir de los datos de la etiqueta."""

import fitz

from modules import barcode_render

# Medidas fisicas de la cinta continua de 29 mm.
TAPE_WIDTH_MM = 29
# Ancho util seguro, para no pasar el limite fisico de impresion de la Brother.
PRINTABLE_WIDTH_MM = 25
# Alto de cada etiqueta dentro de la tira.
LABEL_HEIGHT_MM = 18

_MM = 72 / 25.4
_FONT = "helv"
_BOLD_FONT = "hebo"
_LINE_FACTOR = 1.18

# Alto de las barras y limites del cuerpo tipografico del nombre, en puntos.
_BARS_HEIGHT_PT = 16.0
_NAME_MAX_SIZE_PT = 8.5
_NAME_MIN_SIZE_PT = 3.5
_NAME_MAX_LINES = 4
# Cuerpo base del numero legible; el factor configurable lo multiplica.
_NUMBER_BASE_SIZE_PT = 5.0
_PRICE_SIZE_PT = 9.0


def build_strip(labels, output_path, print_price=True, print_barcode_number=True, number_scale=1.0):
    """Arma la tira continua con una etiqueta debajo de la otra.

    Args:
        labels: lista de dicts con 'barcode', 'name' y 'price'.
        output_path: ruta del PDF a generar.
        print_price: False para no imprimir el precio.
        print_barcode_number: False para no imprimir el número debajo de las barras.
        number_scale: factor de ampliación del número legible.

    Returns:
        La ruta del PDF generado.

    Raises:
        ValueError: si algún código de barras no puede codificarse.
    """
    width_pt = TAPE_WIDTH_MM * _MM
    height_pt = LABEL_HEIGHT_MM * _MM

    doc = fitz.open()
    page = doc.new_page(width=width_pt, height=len(labels) * height_pt)
    try:
        for index, label in enumerate(labels):
            _draw_label(page, label, index * height_pt, print_price, print_barcode_number, number_scale)
        doc.save(output_path)
    finally:
        doc.close()
    return output_path


def _draw_label(page, label, top, print_price, print_barcode_number, number_scale):
    """Dibuja una etiqueta completa a partir del borde superior indicado."""
    width_pt = TAPE_WIDTH_MM * _MM
    printable_pt = PRINTABLE_WIDTH_MM * _MM
    left = (width_pt - printable_pt) / 2
    right = left + printable_pt
    bottom = top + LABEL_HEIGHT_MM * _MM

    barcode = label.get("barcode") or ""
    price = (label.get("price") or "") if print_price else ""
    number_size = _NUMBER_BASE_SIZE_PT * number_scale

    # Se reserva lo que ocupan barras, número y precio; el nombre usa el resto.
    reserved = 0.0
    if barcode:
        reserved += _BARS_HEIGHT_PT + 1.0
        if print_barcode_number:
            reserved += number_size * _LINE_FACTOR
    if price:
        reserved += _PRICE_SIZE_PT * _LINE_FACTOR

    y = top + 1.5
    name_height = max(0.0, bottom - 1.5 - reserved - y)
    if label.get("name") and name_height > _NAME_MIN_SIZE_PT:
        y = _draw_name(page, label["name"], left, right, y, name_height)

    if barcode:
        bars_rect = fitz.Rect(left, y + 1.0, right, y + 1.0 + _BARS_HEIGHT_PT)
        pattern, _ = barcode_render.modules(barcode)
        barcode_render.draw_bars(page, bars_rect, pattern)
        y = bars_rect.y1

        if print_barcode_number:
            y += number_size
            _draw_centered(page, barcode, left, right, y, number_size, _FONT)
            y += number_size * (_LINE_FACTOR - 1)

    if price:
        _draw_centered(page, price, left, right, bottom - 1.5, _PRICE_SIZE_PT, _BOLD_FONT)


def _draw_name(page, name, left, right, top, height):
    """Escribe el nombre ajustando cuerpo y cortes de línea al espacio disponible.

    Args:
        page: página de PyMuPDF donde dibujar.
        name: nombre del producto.
        left: borde izquierdo del área imprimible.
        right: borde derecho del área imprimible.
        top: coordenada y donde empieza el bloque del nombre.
        height: alto disponible para el nombre.

    Returns:
        La coordenada y donde termina el texto escrito.
    """
    width = right - left

    size = _NAME_MAX_SIZE_PT
    lines = _wrap(name, width, size)
    while size > _NAME_MIN_SIZE_PT and (
        len(lines) > _NAME_MAX_LINES or len(lines) * size * _LINE_FACTOR > height
    ):
        size -= 0.25
        lines = _wrap(name, width, size)

    lines = lines[:_NAME_MAX_LINES]
    y = top
    for line in lines:
        y += size
        _draw_centered(page, line, left, right, y, size, _FONT)
        y += size * (_LINE_FACTOR - 1)
    return y


def _wrap(text, width, size):
    """Corta el texto en líneas que entren en el ancho dado."""
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or fitz.get_text_length(candidate, _FONT, size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_centered(page, text, left, right, baseline, size, fontname):
    """Escribe una línea centrada horizontalmente sobre la línea base indicada."""
    text_width = fitz.get_text_length(text, fontname, size)
    x = left + max(0.0, (right - left - text_width) / 2)
    page.insert_text(fitz.Point(x, baseline), text, fontsize=size, fontname=fontname)
