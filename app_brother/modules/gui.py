"""Interfaz gráfica para imprimir etiquetas en la impresora Brother QL-800."""

import json
import os
from tkinter import filedialog

import customtkinter as ctk

from modules import pdf_extract
from modules import printer


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

        self.pdf_path = None
        self.labels = []
        self.printers_by_display = {}
        self.settings_path = "brother_settings.json"

        # Cargar configuraciones guardadas
        self._load_settings()

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
        ctk.CTkLabel(
            self,
            text="Impresor Brother QL-800",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 12))

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
            self, text="Cargar PDF de Etiquetas", command=self._load_pdf, height=40
        ).pack(pady=(16, 4))

        self.info_label = ctk.CTkLabel(
            self, text="Ningún PDF cargado", font=ctk.CTkFont(size=13)
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
            command=self._on_barcode_number_toggle
        ).pack(pady=(4, 0))

        scale_frame = ctk.CTkFrame(self, fg_color="transparent")
        scale_frame.pack(pady=(6, 0))
        ctk.CTkLabel(scale_frame, text="Tamaño del número:").pack(side="left", padx=(0, 8))
        self.barcode_scale_entry = ctk.CTkEntry(scale_frame, width=60, justify="center")
        self.barcode_scale_entry.insert(0, f"{self.saved_barcode_scale:g}")
        self.barcode_scale_entry.pack(side="left")
        self.barcode_scale_entry.bind("<Return>", lambda event: self._on_barcode_scale_change())
        self.barcode_scale_entry.bind("<FocusOut>", lambda event: self._on_barcode_scale_change())
        ctk.CTkLabel(scale_frame, text="x").pack(side="left", padx=(6, 0))
        self._update_barcode_scale_state()

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
        """Devuelve el factor de ampliación del número tipeado en la GUI, ya validado.

        Returns:
            Float entre BARCODE_NUMBER_SCALE_MIN y BARCODE_NUMBER_SCALE_MAX; si el
            campo no existe todavía o tiene un valor inválido, el valor por defecto.
        """
        try:
            value = float(self.barcode_scale_entry.get().strip().replace(",", "."))
        except (AttributeError, ValueError):
            return BARCODE_NUMBER_SCALE
        return min(max(value, BARCODE_NUMBER_SCALE_MIN), BARCODE_NUMBER_SCALE_MAX)

    def _on_barcode_scale_change(self):
        """Normaliza lo tipeado en el campo de tamaño y guarda la preferencia."""
        value = self._barcode_scale()
        self.barcode_scale_entry.delete(0, "end")
        self.barcode_scale_entry.insert(0, f"{value:g}")
        self._save_settings()

    def _update_barcode_scale_state(self):
        """Habilita el campo de tamaño sólo cuando se imprime el número del código."""
        state = "normal" if self.print_barcode_number_var.get() else "disabled"
        self.barcode_scale_entry.configure(state=state)

    def _on_barcode_number_toggle(self):
        """Se activa al tildar o destildar la impresión del número del código."""
        self._update_barcode_scale_state()
        self._save_settings()

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
            self.info_label.configure(text="Ningún PDF cargado")
            self._set_preview("")
            self.name_entry.delete(0, "end")
            self.print_button.configure(state="disabled")
            return

        count = len(self.labels)
        filename = self.pdf_path.rsplit("/", 1)[-1] if self.pdf_path else "Archivo cargado"
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
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, first["name"])
        self.print_button.configure(state="normal")

    def _load_pdf(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF de etiquetas",
            filetypes=[
                ("Archivos PDF", "*.pdf"),
                ("Todos", "*.*"),
            ],
        )
        if not path:
            return

        try:
            self._set_status("Leyendo PDF...", "gray")
            self.labels = pdf_extract.extract_labels(path)
            self.pdf_path = path
            self._update_info_and_preview()
            self._set_status("PDF cargado. Listo para imprimir.", "green")
        except Exception as e:
            self.pdf_path = None
            self.labels = []
            self._update_info_and_preview()
            self._set_status(f"No se pudo cargar el archivo: {e}", "red")
            return

    def _enlarge_barcode_number(self, page, barcode, scale=None):
        """Redibuja el número legible del código de barras con una tipografía más grande.

        El número se agranda hacia arriba desde su línea base original, sin invadir
        el espacio de la imagen del código de barras ni salirse del ancho de la página.

        Args:
            page: página de PyMuPDF a modificar.
            barcode: dígitos del código de barras a ubicar dentro de la página.
            scale: factor de ampliación sobre el tamaño original; si es None se toma
                el valor configurado en la GUI.
        """
        import fitz

        if scale is None:
            scale = self._barcode_scale()

        blocks = page.get_text("dict")["blocks"]

        span = None
        for block in blocks:
            for line in block.get("lines", []):
                for candidate in line["spans"]:
                    if candidate["text"].strip() == barcode:
                        span = candidate
                        break

        if span is None:
            return

        rect = fitz.Rect(span["bbox"])
        origin_x, baseline_y = span["origin"]
        original_size = span["size"]

        # Lo más bajo que llega el contenido que está por encima (la imagen del código).
        top_limit = 0.0
        for block in blocks:
            block_rect = fitz.Rect(block["bbox"])
            if block_rect.y1 <= rect.y0 + 0.5:
                top_limit = max(top_limit, block_rect.y1)

        # Los dígitos crecen desde la línea base hacia arriba (~0.75 del cuerpo tipográfico).
        max_by_height = (baseline_y - top_limit - 1.0) / 0.75
        unit_width = fitz.get_text_length(barcode, fontname="helv", fontsize=1)
        max_by_width = (page.rect.width - origin_x - 2.0) / unit_width if unit_width else original_size
        new_size = min(original_size * scale, max_by_height, max_by_width)

        if new_size <= original_size * 1.02:
            return  # no hay espacio para agrandarlo, se deja como está

        white_rect = fitz.Rect(
            rect.x0 - 1,
            max(rect.y0 - 1, top_limit + 0.2),
            rect.x1 + 1,
            rect.y1 + 1,
        )
        page.draw_rect(white_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        page.insert_text(
            fitz.Point(origin_x, baseline_y),
            barcode,
            fontsize=new_size,
            fontname="helv",
            color=(0, 0, 0),
        )

    def _prepare_pdf_for_printing(self, original_pdf_path, print_price, labels=None, print_barcode_number=True, override_name=None):
        """Prepara el PDF tapando el precio (si print_price es False), aplicando un margen de seguridad física horizontal de 2 mm a cada lado y reescalándolo a 29 mm de ancho y el alto óptimo de tira continua (15 mm)."""
        import fitz
        
        doc = fitz.open(original_pdf_path)
        new_doc = fitz.open()
        
        # Ancho físico de la página de la etiqueta (29 mm)
        target_width_pt = 29 * 72 / 25.4  # ~82.2 pt
        # Ancho útil imprimible seguro (25 mm) para evitar el límite físico de impresión de 27 mm de la Brother
        printable_width_pt = 25 * 72 / 25.4  # ~70.9 pt
        
        # Al imprimir como tira continua consolidada, usamos siempre alto de 15 mm para espacio mínimo
        height_mm = 15
        target_height_pt = height_mm * 72 / 25.4  # ~42.5 pt
        
        # Margen horizontal de seguridad para centrar el contenido imprimible (~5.6 pt)
        x_offset = (target_width_pt - printable_width_pt) / 2
        
        try:
            num_pages = len(doc)
            total_height_pt = num_pages * target_height_pt
            
            # Crear una única página larga para evitar que CUPS corte entre etiquetas
            new_page = new_doc.new_page(width=target_width_pt, height=total_height_pt)
            
            for i, page in enumerate(doc):
                # 1. Tapar precio si corresponde
                if not print_price:
                    rects = page.search_for("$")
                    for r in rects:
                        extended_rect = fitz.Rect(0, r.y0 - 2, page.rect.width, r.y1 + 2)
                        page.draw_rect(extended_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

                # 2. Tapar o agrandar el número del código de barras
                if labels and i < len(labels) and labels[i]["barcode"]:
                    if not print_barcode_number:
                        rects = page.search_for(labels[i]["barcode"])
                        for r in rects:
                            extended_rect = fitz.Rect(0, r.y0 - 2, page.rect.width, r.y1 + 2)
                            page.draw_rect(extended_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
                    else:
                        self._enlarge_barcode_number(page, labels[i]["barcode"])

                # 2.5. Reemplazar el nombre original si se especificó uno editado
                if override_name and labels and i < len(labels):
                    name_lines = labels[i].get("name_lines") or []
                    line_rects = [
                        r for line in name_lines for r in page.search_for(line)
                    ]
                    if line_rects:
                        name_rect = line_rects[0]
                        for r in line_rects[1:]:
                            name_rect.include_rect(r)
                        extended_rect = fitz.Rect(
                            0, name_rect.y0 - 2, page.rect.width, name_rect.y1 + 2
                        )
                        page.draw_rect(
                            extended_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True
                        )
                        text_unit_width = fitz.get_text_length(
                            override_name, fontname="helv", fontsize=1
                        )
                        font_by_width = (extended_rect.width * 0.92) / text_unit_width
                        font_by_height = (extended_rect.height * 0.9) / 1.15
                        font_size = max(6, min(14, font_by_width, font_by_height))
                        page.insert_textbox(
                            extended_rect,
                            override_name,
                            fontsize=font_size,
                            fontname="helv",
                            align=1,
                        )

                # 3. Conservamos el 100% de la página original (sin recortes para evitar cortes de texto)
                orig_rect = page.rect
                clip_rect = orig_rect

                # 4. Calcular la altura proporcional de acuerdo con el ancho útil imprimible de 25 mm
                content_height_pt = printable_width_pt * (clip_rect.height / clip_rect.width)
                
                # Centrar verticalmente el contenido útil dentro del alto de la página de 15 mm
                y_start = i * target_height_pt
                y_offset = y_start + max(0.0, (target_height_pt - content_height_pt) / 2)
                
                # Rectángulo de dibujo con márgenes seguros
                draw_rect = fitz.Rect(x_offset, y_offset, x_offset + printable_width_pt, y_offset + content_height_pt)
                
                # Dibujar en la página larga en las coordenadas específicas
                new_page.show_pdf_page(draw_rect, doc, page.number, clip=clip_rect)

            # Guardamos el PDF temporal resultante en un archivo fijo
            dir_name = os.path.dirname(original_pdf_path) or "."
            temp_pdf_path = os.path.join(dir_name, "brother_temp_print.pdf")
            new_doc.save(temp_pdf_path)
            return temp_pdf_path
        except Exception as e:
            print(f"Error al preparar el PDF para impresión: {e}")
            return original_pdf_path
        finally:
            doc.close()
            new_doc.close()

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

        try:
            self._set_status(f"Enviando a {target['name']}...", "gray")
            self.print_button.configure(state="disabled")

            # Preparar archivo consolidando las etiquetas en tira continua de 15mm
            temp_file = self._prepare_pdf_for_printing(
                self.pdf_path,
                self.print_price_var.get(),
                labels=self.labels,
                print_barcode_number=self.print_barcode_number_var.get(),
                override_name=override_name,
            )

            # Imprimir PDF nativo directamente sin corte automático intermedio (sólo al final de la tira)
            job_id = printer.print_pdf(temp_file, target["name"], auto_cut=False)
            self._set_status(f"Impreso correctamente ({job_id}).", "green")
        except Exception as e:
            self._set_status(f"Error al imprimir: {e}", "red")
        finally:
            self.print_button.configure(state="normal")
