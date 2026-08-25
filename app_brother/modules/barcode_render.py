"""Generacion del codigo de barras cuando el codigo se edita desde la GUI."""

import barcode
import fitz

# Simbologia segun la cantidad de digitos; cualquier otro largo cae en Code 128.
_SYMBOLOGY_BY_LENGTH = {
    13: "ean13",
    12: "upca",
    8: "ean8",
}

# Módulos en blanco a cada lado para que el escáner reconozca inicio y fin.
QUIET_ZONE_MODULES = 8


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


def modules(code):
    """Devuelve el patrón de barras del código, para dibujarlo como vectores.

    No usa los writers de python-barcode a propósito: el de imagen depende de
    Pillow, que no está en el ejecutable, y el vectorial imprime más nítido.

    Args:
        code: dígitos del código de barras a codificar.

    Returns:
        Tupla (patrón de '1' y '0' con un carácter por módulo, código codificado).
        El código devuelto puede diferir del pedido si la simbología recalcula
        el dígito verificador.

    Raises:
        ValueError: si el código no puede codificarse en ninguna simbología.
    """
    generator = barcode.get(symbology(code), code)
    return generator.build()[0], generator.get_fullcode()


def draw_bars(page, rect, pattern):
    """Dibuja las barras del código dentro de un rectángulo, como vectores.

    Los rectángulos van sin trazo: el borde de 1 pt que dibuja PyMuPDF por
    defecto ensancha cada barra y el código deja de leerse.

    Args:
        page: página de PyMuPDF donde dibujar.
        rect: rectángulo que ocupa el código, zona muda incluida.
        pattern: patrón de '1' y '0', un carácter por módulo.
    """
    module_width = rect.width / (len(pattern) + 2 * QUIET_ZONE_MODULES)
    x = rect.x0 + QUIET_ZONE_MODULES * module_width

    run_start = None
    for index, module in enumerate(pattern + "0"):
        if module == "1" and run_start is None:
            run_start = index
        elif module == "0" and run_start is not None:
            bar = fitz.Rect(x + (run_start - index) * module_width, rect.y0, x, rect.y1)
            page.draw_rect(bar, color=None, fill=(0, 0, 0), width=0, overlay=True)
            run_start = None
        x += module_width
