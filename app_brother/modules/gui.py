"""Interfaz gráfica para imprimir etiquetas en la impresora Brother QL-800."""

import json
import os
from tkinter import filedialog

import customtkinter as ctk

from modules import barcode_render
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
            self.info_label.configure(text="Ningún PDF cargado")
            self._set_preview("")
            self.barcode_entry.delete(0, "end")
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
        self.barcode_entry.delete(0, "end")
        self.barcode_entry.insert(0, first["barcode"])
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

    def _redraw_barcode_number(self, page, barcode, new_text=None, scale=None, draw=True):
        """Tapa el número legible original y lo vuelve a dibujar más grande.

        El número se agranda hacia arriba desde su línea base original, sin invadir
        el espacio de la imagen del código de barras ni salirse del ancho de la página.
        Ubica el texto por coincidencia exacta del span, así un código corto que
        aparece dentro del nombre o de la referencia interna no las afecta.

        Args:
            page: página de PyMuPDF a modificar.
            barcode: dígitos originales, para ubicar el texto dentro de la página.
            new_text: texto a dibujar en lugar del original; None para redibujar el mismo.
            scale: factor de ampliación sobre el tamaño original; si es None se toma
                el valor configurado en la GUI.
            draw: False para sólo taparlo, sin volver a dibujarlo.
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

        text = new_text if new_text is not None else barcode

        # Los dígitos crecen desde la línea base hacia arriba (~0.75 del cuerpo tipográfico).
        max_by_height = (baseline_y - top_limit - 1.0) / 0.75
        unit_width = fitz.get_text_length(text, fontname="helv", fontsize=1)
        max_by_width = (page.rect.width - origin_x - 2.0) / unit_width if unit_width else original_size
        new_size = max(min(original_size * scale, max_by_height, max_by_width), original_size)

        if draw and new_text is None and new_size <= original_size * 1.02:
            return  # no hay espacio para agrandarlo, se deja como está

        white_rect = fitz.Rect(
            rect.x0 - 1,
            max(rect.y0 - 1, top_limit + 0.2),
            max(rect.x1, rect.x0 + new_size * unit_width) + 1,
            rect.y1 + 1,
        )
        page.draw_rect(white_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

        if not draw:
            return

        page.insert_text(
            fitz.Point(origin_x, baseline_y),
            text,
            fontsize=new_size,
            fontname="helv",
            color=(0, 0, 0),
        )

    def _replace_barcode_image(self, page, png_bytes):
        """Tapa el código de barras original de Odoo y dibuja el nuevo en su lugar.

        Args:
            page: página de PyMuPDF a modificar.
            png_bytes: imagen del código de barras nuevo, ya generada.
        """
        import fitz

        images = page.get_images(full=True)
        if not images:
            return

        rect = max((page.get_image_bbox(img) for img in images), key=lambda r: r.get_area())
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        page.insert_image(rect, stream=png_bytes, keep_proportion=False, overlay=True)

    def _prepare_pdf_for_printing(self, original_pdf_path, print_price, labels=None, print_barcode_number=True, override_name=None, override_barcode=None):
        """Prepara el PDF tapando el precio (si print_price es False), aplicando un margen de seguridad física horizontal de 2 mm a cada lado y reescalándolo a 29 mm de ancho y el alto óptimo de tira continua (15 mm)."""
        import fitz

        override_barcode_png = None
        if override_barcode:
            override_barcode_png, override_barcode = barcode_render.render_png(override_barcode)
        
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

                # 2. Reemplazar, tapar o agrandar el código de barras y su número
                if labels and i < len(labels) and labels[i]["barcode"]:
                    if override_barcode_png:
                        self._replace_barcode_image(page, override_barcode_png)
                        self._redraw_barcode_number(
                            page,
                            labels[i]["barcode"],
                            new_text=override_barcode,
                            draw=print_barcode_number,
                        )
                    elif not print_barcode_number:
                        rects = page.search_for(labels[i]["barcode"])
                        for r in rects:
                            extended_rect = fitz.Rect(0, r.y0 - 2, page.rect.width, r.y1 + 2)
                            page.draw_rect(extended_rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
                    else:
                        self._redraw_barcode_number(page, labels[i]["barcode"])

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

            # Preparar archivo consolidando las etiquetas en tira continua de 15mm
            temp_file = self._prepare_pdf_for_printing(
                self.pdf_path,
                self.print_price_var.get(),
                labels=self.labels,
                print_barcode_number=self.print_barcode_number_var.get(),
                override_name=override_name,
                override_barcode=override_barcode,
            )

            # Imprimir PDF nativo directamente sin corte automático intermedio (sólo al final de la tira)
            job_id = printer.print_pdf(temp_file, target["name"], auto_cut=False)
            self._set_status(
                f"Impreso correctamente ({job_id}).{barcode_notice}",
                "orange" if barcode_notice else "green",
            )
        except Exception as e:
            self._set_status(f"Error al imprimir: {e}", "red")
        finally:
            self.print_button.configure(state="normal")
