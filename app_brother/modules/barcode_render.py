"""Generacion del codigo de barras cuando el codigo se edita desde la GUI."""

import io

import barcode
from barcode.writer import ImageWriter

# Simbologia segun la cantidad de digitos; cualquier otro largo cae en Code 128.
_SYMBOLOGY_BY_LENGTH = {
    13: "ean13",
    12: "upca",
    8: "ean8",
}

_WRITER_OPTIONS = {
    "module_height": 12.0,
    "quiet_zone": 1.0,
    "write_text": False,
}


def symbology(code):
    """Devuelve el nombre de la simbologia que corresponde a un codigo.

    Args:
        code: dígitos del código de barras.

    Returns:
        Nombre de la simbología ('ean13', 'upca', 'ean8' o 'code128').
    """
    if not code.isdigit():
        return "code128"
    return _SYMBOLOGY_BY_LENGTH.get(len(code), "code128")


def encoded_code(code):
    """Devuelve el código tal como va a quedar codificado en las barras.

    Args:
        code: dígitos del código de barras.

    Returns:
        El código final; difiere del pedido cuando la simbología recalcula el
        dígito verificador (por ejemplo un EAN-13 tipeado con el dígito mal).

    Raises:
        ValueError: si el código no puede codificarse en ninguna simbología.
    """
    return barcode.get(symbology(code), code).get_fullcode()


def render_png(code):
    """Dibuja el código de barras (sólo barras, sin número legible) como PNG.

    Args:
        code: dígitos del código de barras a codificar.

    Returns:
        Tupla (bytes del PNG, código realmente codificado). El código devuelto
        puede diferir del pedido si la simbología recalcula el dígito verificador.

    Raises:
        ValueError: si el código no puede codificarse en ninguna simbología.
    """
    name = symbology(code)
    generator = barcode.get(name, code, writer=ImageWriter())
    buffer = io.BytesIO()
    generator.write(buffer, options=dict(_WRITER_OPTIONS))
    return buffer.getvalue(), generator.get_fullcode()
