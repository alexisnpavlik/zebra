"""Generacion de etiquetas en lenguaje ZPL (Zebra ZD421 y similares)."""

from config import config
from modules.label_text import (
    barcode_digits,
    clean_text,
    normalize_price,
    truncate_name,
)

# Posiciones dentro de una etiqueta, en dots (relativas a la columna).
_BARCODE_X = 8
_BARCODE_Y = 4
_NAME_Y = 70
_PRICE_Y = 96

# Alto/ancho de fuente para el nombre (^A0).
_NAME_HEIGHT = 20
_NAME_WIDTH = 10

# Hasta esta longitud el precio se imprime en tamano grande.
_PRICE_WIDE_MAX_CHARS = 8


def row_header():
    """Comandos ZPL que abren una fila de etiquetas."""
    return (
        "^XA\r\n"
        f"^PW{config.ROW_WIDTH_DOTS}\r\n"
        f"^LL{config.LABEL_HEIGHT_DOTS}\r\n"
    )


def row_footer():
    """Comando ZPL que cierra e imprime la fila."""
    return "^XZ\r\n"


def build_label(label, x, print_price=True, print_barcode_number=True):
    """Comandos ZPL de una etiqueta en la columna que inicia en x."""
    parts = _barcode(label["barcode"], x, print_barcode_number) + _name(label["name"], x)
    if print_price:
        parts += _price(label["price"], x)
    return parts


def _centered_text(text, x, y, height, width):
    """Campo de texto centrado en el ancho de la etiqueta via ^FB."""
    return (
        f"^FO{x},{y}^A0N,{height},{width}"
        f"^FB{config.LABEL_WIDTH_DOTS},1,0,C,0^FD{text}^FS\r\n"
    )


def _barcode(barcode, x, print_barcode_number=True):
    hr = "Y" if print_barcode_number else "N"
    digits = barcode_digits(barcode)
    bx = x + _BARCODE_X
    if len(digits) == 13:
        # ^BE = EAN-13; usa 12 digitos, el 13ro es verificador calculado.
        return f"^FO{bx},{_BARCODE_Y}^BY2^BEN,40,{hr},N^FD{digits[:12]}^FS\r\n"
    # Sin un EAN valido se cae a Code 128.
    data = clean_text(barcode) or "0"
    return f"^FO{bx},{_BARCODE_Y}^BY2^BCN,40,{hr},N,N^FD{data}^FS\r\n"


def _name(name, x):
    text = truncate_name(name)
    return _centered_text(text, x, _NAME_Y, _NAME_HEIGHT, _NAME_WIDTH)


def _price(price, x):
    text = normalize_price(price)
    if len(text) <= _PRICE_WIDE_MAX_CHARS:
        height, width = 48, 24
    else:
        height, width = 40, 16
    return _centered_text(text, x, _PRICE_Y, height, width)
