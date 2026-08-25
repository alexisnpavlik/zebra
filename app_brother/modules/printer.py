"""Módulo de detección de impresoras e impresión nativa de PDFs (Brother y estándar)."""

import os
import shutil
import subprocess
import sys

if sys.platform == "win32":
    try:
        import win32print
    except ImportError:
        win32print = None


def list_printers():
    """Lista todas las impresoras disponibles en el sistema.

    Returns:
        Lista de dicts con 'name' y 'ready' (bool).
    """
    if sys.platform == "win32":
        return _list_printers_windows()
    return _list_printers_cups()


def print_pdf(pdf_path, printer_name, auto_cut=True, segment_height_pt=None):
    """Envía un archivo PDF a la impresora seleccionada a través del controlador del sistema.

    Args:
        pdf_path: ruta absoluta o relativa al archivo PDF.
        printer_name: nombre de la cola de impresión de destino.
        auto_cut: True para cortar después de cada etiqueta, False para cortar sólo al final de la tira.
        segment_height_pt: alto de cada etiqueta dentro de la tira, en puntos. En
            Windows la tira se manda etiqueta por etiqueta para que el driver no
            recorte la parte que no entra en una página.

    Returns:
        Identificador o mensaje del trabajo enviado.

    Raises:
        RuntimeError: si el envío falla o no se cuenta con los comandos necesarios.
    """
    if sys.platform == "win32":
        return _print_pdf_windows(pdf_path, printer_name, segment_height_pt)
    return _print_pdf_cups(pdf_path, printer_name, auto_cut)


# --- Linux / macOS (CUPS) ---

def _list_printers_cups():
    if shutil.which("lpstat") is None:
        return []
    try:
        result = subprocess.run(
            ["lpstat", "-p"], capture_output=True, text=True, timeout=10
        )
    except (subprocess.SubprocessError, OSError):
        return []

    printers = []
    for line in result.stdout.splitlines():
        if not line.startswith("printer "):
            continue
        name = line.split()[1]
        printers.append({
            "name": name,
            "ready": "disabled" not in line,
        })
    return printers


def _print_pdf_cups(pdf_path, printer_name, auto_cut=True):
    if shutil.which("lp") is None:
        raise RuntimeError("No se encontró el comando 'lp' (CUPS no está instalado).")
    
    cut_opt = "AutoCut=True" if auto_cut else "AutoCut=False"
    try:
        result = subprocess.run(
            ["lp", "-d", printer_name, "-o", "PageSize=29mm", "-o", cut_opt, pdf_path],
            capture_output=True,
            timeout=60,
        )
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Fallo al ejecutar lp: {e}") from e

    if result.returncode != 0:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"La impresora rechazó el trabajo: {error}")

    job_id = result.stdout.decode("utf-8", errors="replace").strip()
    print(f"PDF enviado a '{printer_name}': {job_id}")
    return job_id


# --- Windows (ShellExecute / win32api) ---

def _list_printers_windows():
    if win32print is None:
        return []
    printers = []
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    for _, _, name, _ in win32print.EnumPrinters(flags):
        printers.append({
            "name": name,
            "ready": True,
        })
    return printers


def _print_pdf_windows(pdf_path, printer_name, segment_height_pt=None):
    """Dibuja el PDF en el contexto del driver de Windows y lo manda a imprimir.

    No usa el verbo 'printto' de ShellExecute: ese depende de que haya un lector
    de PDF registrado en el sistema y falla con el error 31 cuando no lo hay.
    """
    try:
        import fitz
        import win32con
        import win32ui
        from PIL import Image, ImageWin
    except ImportError as e:
        raise RuntimeError(
            f"Falta un módulo para imprimir en Windows ({e}). "
            "Ejecuta: pip install pywin32 pillow"
        ) from e

    doc = fitz.open(pdf_path)
    hdc = win32ui.CreateDC()
    try:
        hdc.CreatePrinterDC(printer_name)
        device_width = hdc.GetDeviceCaps(win32con.HORZRES)
        dpi = hdc.GetDeviceCaps(win32con.LOGPIXELSX) or 300

        hdc.StartDoc(os.path.basename(pdf_path))
        for page in doc:
            for clip in _segments(page, segment_height_pt):
                pixmap = page.get_pixmap(dpi=dpi, clip=clip)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                height = int(image.height * device_width / image.width)

                hdc.StartPage()
                ImageWin.Dib(image).draw(hdc.GetHandleOutput(), (0, 0, device_width, height))
                hdc.EndPage()
        hdc.EndDoc()
    except Exception as e:
        raise RuntimeError(f"Error al imprimir en Windows: {e}") from e
    finally:
        doc.close()
        hdc.DeleteDC()

    return "Trabajo enviado a la cola de Windows"


def _segments(page, segment_height_pt):
    """Divide una página en franjas de alto fijo, una por etiqueta.

    Args:
        page: página de PyMuPDF.
        segment_height_pt: alto de cada etiqueta en puntos, o None para no dividir.

    Returns:
        Lista de fitz.Rect a imprimir, en orden.
    """
    import fitz

    if not segment_height_pt or segment_height_pt <= 0:
        return [page.rect]

    rects = []
    top = page.rect.y0
    while top < page.rect.y1 - 0.5:
        bottom = min(top + segment_height_pt, page.rect.y1)
        rects.append(fitz.Rect(page.rect.x0, top, page.rect.x1, bottom))
        top = bottom
    return rects
