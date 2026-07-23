"""Interfaz grafica para imprimir etiquetas desde un PDF."""

from tkinter import filedialog

import customtkinter as ctk

from config import config
from modules import pdf_extract, txt_extract
from modules.label_layout import build_print_job
from modules import printer


def _display_name(printer_info):
    """Texto que se muestra en el desplegable para una impresora."""
    estado = "" if printer_info["ready"] else "  - sin conexion"
    return f"{printer_info['name']} ({printer_info['language'].upper()}){estado}"


class LabelPrinterApp(ctk.CTk):
    """Ventana principal del impresor de etiquetas."""

    def __init__(self):
        super().__init__()
        self.title("Impresor de etiquetas Zebra")
        self.geometry("520x600")
        self.resizable(False, False)

        # Cargar icono de la aplicación
        try:
            import os
            import sys
            from PIL import Image, ImageTk
            
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            icon_path = os.path.join(base_path, "assets", "zebra_logo.png")
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon_image)
                self.wm_iconphoto(True, photo)
                self._icon_ref = photo
        except Exception as e:
            print(f"No se pudo cargar el icono: {e}")

        self.pdf_path = None
        self.labels = []
        self.printers_by_display = {}

        self._build_widgets()
        self._refresh_printers()

    def _build_widgets(self):
        ctk.CTkLabel(
            self,
            text="Impresor de etiquetas Zebra",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 12))

        # --- Seleccion de impresora ---
        printer_frame = ctk.CTkFrame(self)
        printer_frame.pack(pady=4, padx=20, fill="x")

        ctk.CTkLabel(printer_frame, text="Impresora:").pack(
            side="left", padx=(12, 8), pady=10
        )
        self.printer_menu = ctk.CTkOptionMenu(
            printer_frame, values=["(detectando...)"], width=260
        )
        self.printer_menu.pack(side="left", pady=10)
        ctk.CTkButton(
            printer_frame, text="Actualizar", width=90,
            command=self._refresh_printers,
        ).pack(side="left", padx=10, pady=10)

        # --- Carga de PDF ---
        ctk.CTkButton(
            self, text="Cargar PDF / TXT", command=self._load_pdf, height=40
        ).pack(pady=(16, 4))

        self.info_label = ctk.CTkLabel(
            self, text="Ningun PDF cargado", font=ctk.CTkFont(size=13)
        )
        self.info_label.pack(pady=(12, 8))

        self.preview = ctk.CTkTextbox(
            self, width=440, height=120, font=ctk.CTkFont(size=13)
        )
        self.preview.pack(pady=8)
        self.preview.configure(state="disabled")

        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(pady=(0, 8), padx=20, fill="x")
        ctk.CTkLabel(name_frame, text="Nombre (editable):").pack(
            side="left", padx=(12, 8)
        )
        self.name_entry = ctk.CTkEntry(name_frame, width=300)
        self.name_entry.pack(side="left", padx=(0, 0), fill="x", expand=True)

        self.print_price_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text="Imprimir precio",
            variable=self.print_price_var,
        ).pack(pady=(4, 0))

        self.print_barcode_number_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text="Imprimir número de código de barras",
            variable=self.print_barcode_number_var,
        ).pack(pady=(4, 0))

        self.print_button = ctk.CTkButton(
            self,
            text="Imprimir",
            command=self._print,
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            state="disabled",
        )
        self.print_button.pack(pady=12)

        self.status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), wraplength=480
        )
        self.status_label.pack(side="bottom", pady=16)

    def _refresh_printers(self):
        """Detecta las impresoras de CUPS y llena el desplegable."""
        printers = printer.list_printers()
        self.printers_by_display = {_display_name(p): p for p in printers}

        if not printers:
            self.printer_menu.configure(values=["(ninguna detectada)"])
            self.printer_menu.set("(ninguna detectada)")
            self._set_status(
                "No se detectaron impresoras en CUPS.", "orange"
            )
            return

        displays = list(self.printers_by_display)
        self.printer_menu.configure(values=displays)
        self.printer_menu.set(displays[0])
        self._set_status(
            f"{len(printers)} impresora(s) detectada(s).", "green")

    def _selected_printer(self):
        """Devuelve el dict de la impresora elegida, o None."""
        return self.printers_by_display.get(self.printer_menu.get())

    def _set_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)
        self.update_idletasks()

    def _set_preview(self, text):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _load_pdf(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de etiquetas",
            filetypes=[
                ("Etiquetas", "*.pdf *.txt"),
                ("Archivos PDF", "*.pdf"),
                ("Archivos TXT (ZPL)", "*.txt"),
                ("Todos", "*.*"),
            ],
        )
        if not path:
            return

        try:
            if path.lower().endswith(".txt"):
                self._set_status("Leyendo TXT...", "gray")
                self.labels = txt_extract.extract_labels(path)
            else:
                self._set_status("Leyendo PDF...", "gray")
                self.labels = pdf_extract.extract_labels(path)
            self.pdf_path = path
        except Exception as e:
            self.pdf_path = None
            self.labels = []
            self.print_button.configure(state="disabled")
            self.info_label.configure(text="Ningun PDF cargado")
            self._set_preview("")
            self._set_status(f"No se pudo cargar el PDF: {e}", "red")
            return

        count = len(self.labels)
        rows = (count + config.COLUMNS - 1) // config.COLUMNS
        filename = path.rsplit("/", 1)[-1]
        self.info_label.configure(
            text=f"{filename}\n{count} etiqueta(s) - {rows} fila(s) de impresion"
        )

        first = self.labels[0]
        self._set_preview(
            "Vista previa (primera etiqueta):\n\n"
            f"Codigo:  {first['barcode'] or '(no detectado)'}\n"
            f"Nombre:  {first['name'] or '(no detectado)'}\n"
            f"Precio:  {first['price'] or '(no detectado)'}"
        )
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, first["name"])
        self.print_button.configure(state="normal")
        self._set_status("PDF cargado. Listo para imprimir.", "green")

    def _print(self):
        if not self.labels:
            return

        target = self._selected_printer()
        if target is None:
            self._set_status("Elegi una impresora valida.", "red")
            return

        edited_name = self.name_entry.get().strip()
        labels_to_print = self.labels
        if edited_name:
            labels_to_print = [
                {**label, "name": edited_name} for label in self.labels
            ]

        try:
            self._set_status(f"Enviando a {target['name']}...", "gray")
            self.print_button.configure(state="disabled")
            job = build_print_job(
                labels_to_print,
                target["language"],
                print_price=self.print_price_var.get(),
                print_barcode_number=self.print_barcode_number_var.get(),
            )
            job_id = printer.send_raw(job, target["name"])
            self._set_status(f"Impreso correctamente ({job_id}).", "green")
        except Exception as e:
            self._set_status(f"Error al imprimir: {e}", "red")
        finally:
            self.print_button.configure(state="normal")
