"""Generacion del codigo de barras cuando el codigo se edita desde la GUI."""

import barcode

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
