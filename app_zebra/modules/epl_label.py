"""Generacion de etiquetas en lenguaje EPL (Zebra GC420t y similares)."""

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
_NAME_Y = 72
_PRICE_Y = 95

# Hasta esta longitud el precio se imprime en doble ancho.
_PRICE_WIDE_MAX_CHARS = 8

# Ancho de avance por caracter en cada fuente EPL (multiplicador 1), en dots.
# Las fuentes EPL son monoespaciadas, lo que permite centrar el texto.
_CHAR_WIDTH = {1: 10, 2: 12, 3: 14, 4: 16, 5: 34}


def row_header():
    """Comandos EPL que abren una fila de etiquetas."""
    return (
        "N\r\n"
        f"q{config.ROW_WIDTH_DOTS}\r\n"
        f"Q{config.LABEL_HEIGHT_DOTS},{config.GAP_V_DOTS}\r\n"
    )


def row_footer():
    """Comando EPL que imprime la fila."""
    return "P1\r\n"


def build_label(label, x, print_price=True, print_barcode_number=True):
    """Comandos EPL de una etiqueta en la columna que inicia en x."""
    parts = _barcode(label["barcode"], x, print_barcode_number) + _name(label["name"], x)
    if print_price:
        parts += _price(label["price"], x)
    return parts


def _centered_x(text, x, font, h_mult):
    """Posicion X que centra el texto en el ancho de la etiqueta."""
    text_width = len(text) * _CHAR_WIDTH[font] * h_mult
    offset = max(0, (config.LABEL_WIDTH_DOTS - text_width) // 2)
    return x + offset


def _barcode(barcode, x, print_barcode_number=True):
    hr = "B" if print_barcode_number else "N"
    digits = barcode_digits(barcode)
    bx = x + _BARCODE_X
    if len(digits) == 13:
        # E30 = EAN-13; usa 12 digitos, el 13ro es verificador calculado.
        return f'B{bx},{_BARCODE_Y},0,E30,2,2,40,{hr},"{digits[:12]}"\r\n'
    # Sin un EAN valido se cae a Code 128.
    data = clean_text(barcode) or "0"
    return f'B{bx},{_BARCODE_Y},0,1,2,2,40,{hr},"{data}"\r\n'


def _name(name, x):
    text = truncate_name(name)
    nx = _centered_x(text, x, font=2, h_mult=1)
    return f'A{nx},{_NAME_Y},0,2,1,1,N,"{text}"\r\n'


def _price(price, x):
    text = normalize_price(price)
    h_mult = 2 if len(text) <= _PRICE_WIDE_MAX_CHARS else 1
    px = _centered_x(text, x, font=3, h_mult=h_mult)
    return f'A{px},{_PRICE_Y},0,3,{h_mult},2,N,"{text}"\r\n'
