"""Interfaz gráfica para imprimir etiquetas en la impresora Brother QL-800."""

import json
import os
from tkinter import filedialog

import customtkinter as ctk

from modules import barcode_render
from modules import label_render
from modules import printer
from modules import txt_extract


# Factor de ampliacion del numero legible del codigo de barras al imprimir.
BARCODE_NUMBER_SCALE = 1.45
BARCODE_NUMBER_SCALE_MIN = 1.0
BARCODE_NUMBER_SCALE_MAX = 3.0


def _display_name(printer_info):
    """Texto que se muestra en el desplegable para una impresora."""
    estado = "" if printer_info["ready"] else "  - sin conexion"
    return f"{printer_info['name']}{estado}"


class BrotherLabelPrinterApp(ctk.CTk):
    """Ventana principal del impresor de etiquetas Brother QL-800."""

    def __init__(self):
        super().__init__()
        self.title("Impresor de etiquetas Brother QL-800")
        self.geometry("520x640")
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
                
            icon_path = os.path.join(base_path, "assets", "brother_logo.png")
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon_image)
                self.wm_iconphoto(True, photo)
                self._icon_ref = photo
        except Exception as e:
            print(f"No se pudo cargar el icono: {e}")

        self.txt_path = None
        self.labels = []
        self.printers_by_display = {}
        self.settings_window = None
        self.settings_path = "brother_settings.json"

        # Cargar configuraciones guardadas
        self._load_settings()

        self.barcode_scale = self.saved_barcode_scale

        self._build_widgets()
        self._refresh_printers()

    def _load_settings(self):
        """Carga las preferencias del usuario del archivo local json."""
        self.saved_printer = None
        self.saved_print_price = False
        self.saved_print_barcode_number = False
        self.saved_barcode_scale = BARCODE_NUMBER_SCALE

        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.saved_printer = data.get("printer")
                    self.saved_print_price = data.get("print_price", False)
                    self.saved_print_barcode_number = data.get("print_barcode_number", False)
                    self.saved_barcode_scale = data.get("barcode_number_scale", BARCODE_NUMBER_SCALE)
            except Exception as e:
                print(f"Error al cargar brother settings: {e}")

    def _save_settings(self):
        """Guarda las preferencias actuales del usuario en el archivo json."""
        printer_display = self.printer_menu.get() if hasattr(self, "printer_menu") else None
        printer_name = None
        if printer_display and printer_display not in ("(detectando...)", "(ninguna detectada)"):
            p_info = self.printers_by_display.get(printer_display)
            if p_info:
                printer_name = p_info["name"]

        data = {
            "printer": printer_name,
            "print_price": self.print_price_var.get() if hasattr(self, "print_price_var") else False,
            "print_barcode_number": self.print_barcode_number_var.get() if hasattr(self, "print_barcode_number_var") else False,
            "barcode_number_scale": self._barcode_scale(),
        }
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error al guardar brother settings: {e}")

    def _build_widgets(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(
            header,
            text="Impresor Brother QL-800",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", expand=True)
        ctk.CTkButton(
            header,
            text="⚙",
            width=36,
            height=32,
            font=ctk.CTkFont(size=18),
            command=self._open_settings,
        ).pack(side="right")

        # --- Selección de impresora ---
        printer_frame = ctk.CTkFrame(self)
        printer_frame.pack(pady=4, padx=20, fill="x")

        ctk.CTkLabel(printer_frame, text="Impresora:").pack(
            side="left", padx=(12, 8), pady=10
        )
        self.printer_menu = ctk.CTkOptionMenu(
            printer_frame, values=["(detectando...)"], width=260, command=self._on_printer_change
        )
        self.printer_menu.pack(side="left", pady=10)
        ctk.CTkButton(
            printer_frame, text="Actualizar", width=90,
            command=self._refresh_printers,
        ).pack(side="left", padx=10, pady=10)

        # --- Carga de PDF ---
        ctk.CTkButton(
            self, text="Cargar TXT de Etiquetas", command=self._load_txt, height=40
        ).pack(pady=(16, 4))

        self.info_label = ctk.CTkLabel(
            self, text="Ningún archivo cargado", font=ctk.CTkFont(size=13)
        )
        self.info_label.pack(pady=(12, 8))

        self.preview = ctk.CTkTextbox(
            self, width=440, height=120, font=ctk.CTkFont(size=13)
        )
        self.preview.pack(pady=8)
        self.preview.configure(state="disabled")

        barcode_frame = ctk.CTkFrame(self, fg_color="transparent")
        barcode_frame.pack(pady=(0, 4), padx=20, fill="x")
        ctk.CTkLabel(barcode_frame, text="Código (editable):").pack(
            side="left", padx=(12, 8)
        )
        self.barcode_entry = ctk.CTkEntry(barcode_frame, width=300)
        self.barcode_entry.pack(side="left", fill="x", expand=True)

        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.pack(pady=(0, 8), padx=20, fill="x")
        ctk.CTkLabel(name_frame, text="Nombre (editable):").pack(
            side="left", padx=(12, 8)
        )
        self.name_entry = ctk.CTkEntry(name_frame, width=300)
        self.name_entry.pack(side="left", padx=(0, 0), fill="x", expand=True)

        self.print_price_var = ctk.BooleanVar(value=self.saved_print_price)
        ctk.CTkCheckBox(
            self,
            text="Imprimir precio",
            variable=self.print_price_var,
            command=self._save_settings
        ).pack(pady=(4, 0))

        self.print_barcode_number_var = ctk.BooleanVar(value=self.saved_print_barcode_number)
        ctk.CTkCheckBox(
            self,
            text="Imprimir número de código de barras",
            variable=self.print_barcode_number_var,
            command=self._save_settings
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

    def _barcode_scale(self):
        """Devuelve el factor de ampliación del número del código, ya validado.

        Returns:
            Float entre BARCODE_NUMBER_SCALE_MIN y BARCODE_NUMBER_SCALE_MAX.
        """
        try:
            value = float(self.barcode_scale)
        except (AttributeError, TypeError, ValueError):
            return BARCODE_NUMBER_SCALE
        return min(max(value, BARCODE_NUMBER_SCALE_MIN), BARCODE_NUMBER_SCALE_MAX)

    def _open_settings(self):
        """Abre la ventana de ajustes de tamaño, fuera de la pantalla principal."""
        if getattr(self, "settings_window", None) is not None and self.settings_window.winfo_exists():
            self.settings_window.focus()
            return

        window = ctk.CTkToplevel(self)
        window.title("Ajustes")
        window.geometry("380x210")
        window.resizable(False, False)
        window.transient(self)
        self.settings_window = window

        ctk.CTkLabel(
            window, text="Ajustes de impresión", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(16, 12))

        row = ctk.CTkFrame(window, fg_color="transparent")
        row.pack(padx=20, fill="x")
        ctk.CTkLabel(row, text="Tamaño del número del código:").pack(side="left")
        scale_entry = ctk.CTkEntry(row, width=60, justify="center")
        scale_entry.insert(0, f"{self._barcode_scale():g}")
        scale_entry.pack(side="left", padx=(8, 4))
        ctk.CTkLabel(row, text="x").pack(side="left")

        ctk.CTkLabel(
            window,
            text=(
                f"Entre {BARCODE_NUMBER_SCALE_MIN:g}x y {BARCODE_NUMBER_SCALE_MAX:g}x sobre el tamaño "
                "original.\nSe aplica sólo si se imprime el número del código."
            ),
            font=ctk.CTkFont(size=11),
            justify="left",
        ).pack(padx=20, pady=(10, 0), anchor="w")

        ctk.CTkButton(
            window, text="Guardar", height=36,
            command=lambda: self._apply_settings(scale_entry.get()),
        ).pack(pady=16)

        window.after(200, window.grab_set)

    def _apply_settings(self, scale_text):
        """Valida lo tipeado en los ajustes, lo guarda y cierra la ventana.

        Args:
            scale_text: factor de ampliación tal como fue tipeado por el usuario.
        """
        try:
            self.barcode_scale = float(scale_text.strip().replace(",", "."))
        except (AttributeError, ValueError):
            self.barcode_scale = BARCODE_NUMBER_SCALE
        self.barcode_scale = self._barcode_scale()
        self._save_settings()

        if getattr(self, "settings_window", None) is not None:
            self.settings_window.destroy()
            self.settings_window = None
        self._set_status(f"Tamaño del número: {self.barcode_scale:g}x", "gray")

    def _refresh_printers(self):
        """Detecta las impresoras del sistema y llena el desplegable."""
        printers = printer.list_printers()
        self.printers_by_display = {_display_name(p): p for p in printers}

        if not printers:
            self.printer_menu.configure(values=["(ninguna detectada)"])
            self.printer_menu.set("(ninguna detectada)")
            self._set_status(
                "No se detectaron impresoras en el sistema.", "orange"
            )
            return

        displays = list(self.printers_by_display)
        self.printer_menu.configure(values=displays)

        # Intentar seleccionar la última impresora guardada
        selected_display = None
        if self.saved_printer:
            for display in displays:
                if self.printers_by_display[display]["name"] == self.saved_printer:
                    selected_display = display
                    break

        if not selected_display and displays:
            selected_display = displays[0]

        if selected_display:
            self.printer_menu.set(selected_display)

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

    def _on_printer_change(self, choice):
        """Se activa al cambiar la impresora en el selector."""
        self._save_settings()

    def _update_info_and_preview(self):
        """Actualiza las etiquetas informativas y la vista previa del PDF cargado."""
        if not self.labels:
            self.info_label.configure(text="Ningún archivo cargado")
            self._set_preview("")
            self.barcode_entry.delete(0, "end")
            self.name_entry.delete(0, "end")
            self.print_button.configure(state="disabled")
            return

        count = len(self.labels)
        filename = self.txt_path.rsplit("/", 1)[-1] if self.txt_path else "Archivo cargado"
        self.info_label.configure(
            text=f"{filename}\n{count} etiqueta(s) individual(es) a imprimir"
        )

        first = self.labels[0]
        self._set_preview(
            "Vista previa (primera etiqueta):\n\n"
            f"Código:  {first['barcode'] or '(no detectado)'}\n"
            f"Nombre:  {first['name'] or '(no detectado)'}\n"
            f"Precio:  {first['price'] or '(no detectado)'}"
        )
        self.barcode_entry.delete(0, "end")
        self.barcode_entry.insert(0, first["barcode"])
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, first["name"])
        self.print_button.configure(state="normal")

    def _load_txt(self):
        """Abre un TXT con las etiquetas ZPL exportadas de Odoo."""
        path = filedialog.askopenfilename(
            title="Seleccionar archivo TXT de etiquetas",
            filetypes=[
                ("Archivos TXT (ZPL)", "*.txt"),
                ("Todos", "*.*"),
            ],
        )
        if not path:
            return

        try:
            self._set_status("Leyendo TXT...", "gray")
            self.labels = txt_extract.extract_labels(path)
            self.txt_path = path
            self._update_info_and_preview()
            self._set_status("TXT cargado. Listo para imprimir.", "green")
        except Exception as e:
            self.txt_path = None
            self.labels = []
            self._update_info_and_preview()
            self._set_status(f"No se pudo cargar el archivo: {e}", "red")

    def _labels_to_print(self, override_name=None, override_barcode=None):
        """Devuelve las etiquetas a imprimir, con las ediciones ya aplicadas.

        Args:
            override_name: nombre editado a usar en todas las etiquetas, o None.
            override_barcode: código editado a usar en todas las etiquetas, o None.

        Returns:
            Lista de dicts lista para dibujar.
        """
        labels = []
        for label in self.labels:
            copy = dict(label)
            if override_name:
                copy["name"] = override_name
            if override_barcode:
                copy["barcode"] = override_barcode
            labels.append(copy)
        return labels

    def _temp_pdf_path(self):
        """Ruta del PDF temporal que se manda a la impresora."""
        dir_name = os.path.dirname(self.txt_path or "") or "."
        return os.path.join(dir_name, "brother_temp_print.pdf")

    def _print(self):
        if not self.labels:
            return

        target = self._selected_printer()
        if target is None:
            self._set_status("Elegí una impresora válida.", "red")
            return

        edited_name = self.name_entry.get().strip()
        original_name = self.labels[0]["name"].strip() if self.labels else ""
        override_name = edited_name if edited_name and edited_name != original_name else None

        edited_barcode = self.barcode_entry.get().strip()
        original_barcode = self.labels[0]["barcode"].strip() if self.labels else ""
        override_barcode = edited_barcode if edited_barcode and edited_barcode != original_barcode else None

        barcode_notice = ""
        if override_barcode:
            try:
                encoded = barcode_render.encoded_code(override_barcode)
            except Exception as e:
                self._set_status(f"Código de barras inválido: {e}", "red")
                return
            if encoded != override_barcode:
                self.barcode_entry.delete(0, "end")
                self.barcode_entry.insert(0, encoded)
                barcode_notice = f" Dígito verificador corregido: se imprimió {encoded}."
                override_barcode = encoded

        try:
            self._set_status(f"Enviando a {target['name']}...", "gray")
            self.print_button.configure(state="disabled")

            # Dibujar la tira continua con las etiquetas, una debajo de la otra
            temp_file = label_render.build_strip(
                self._labels_to_print(override_name, override_barcode),
                self._temp_pdf_path(),
                print_price=self.print_price_var.get(),
                print_barcode_number=self.print_barcode_number_var.get(),
                number_scale=self._barcode_scale(),
            )

            # Imprimir PDF nativo directamente sin corte automático intermedio (sólo al final de la tira)
            job_id = printer.print_pdf(
                temp_file,
                target["name"],
                auto_cut=False,
                segment_height_pt=label_render.LABEL_HEIGHT_MM * 72 / 25.4,
            )
            self._set_status(
                f"Impreso correctamente ({job_id}).{barcode_notice}",
                "orange" if barcode_notice else "green",
            )
        except Exception as e:
            self._set_status(f"Error al imprimir: {e}", "red")
        finally:
            self.print_button.configure(state="normal")
