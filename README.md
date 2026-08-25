# Zebra_label_printer_odoo (Impresor de Etiquetas Zebra)

Aplicación de escritorio para imprimir etiquetas de productos en impresoras Zebra desde archivos PDF o TXT (ZPL) exportados de Odoo.

Soporta etiquetas de 3 columnas (formato 29×20 mm) en lenguaje **EPL** (GC420t y similares) y **ZPL** (ZD421 y similares).

---

## Uso

1. Seleccioná la impresora en el desplegable (o hacé clic en **Actualizar**)
2. Cargá el archivo de etiquetas: la app Zebra acepta PDF o TXT, la app Brother
   trabaja sólo con el **TXT (ZPL)** que exporta Odoo
3. Verificá la vista previa
4. Corregí el código o el nombre en sus campos si hace falta
5. Marcá **Imprimir precio** si querés incluirlo en la etiqueta (desmarcado por defecto)
6. Hacé clic en **Imprimir**

La app Brother no reenvía el archivo de Odoo: lee los datos del TXT y dibuja la
etiqueta de 29 mm ella misma (nombre, código de barras, número y precio). El
tamaño del número se ajusta desde el engranaje.

---

## Windows bloquea el ejecutable

Windows 11 con **Control Inteligente de Aplicaciones** (Smart App Control) bloquea el `.exe`
porque no está firmado digitalmente: no aparece la opción "Ejecutar de todas formas".
Tres caminos, de menor a mayor costo:

1. **Desactivar Smart App Control** en esa PC: Configuración → Privacidad y seguridad →
   Seguridad de Windows → Control de aplicaciones y navegador → Control inteligente de
   aplicaciones → Desactivado. Ojo: una vez desactivado, sólo se puede volver a activar
   reinstalando Windows.
2. **Correr desde el código** en vez del ejecutable: instalar Python 3.11+,
   `pip install -r requirements.txt` y `python app_brother/main.py`.
3. **Firmar el ejecutable**: comprar un certificado code-signing (OV o EV) y cargarlo en
   los Secrets del repo como `WINDOWS_CERT_PFX_BASE64` (el .pfx en base64) y
   `WINDOWS_CERT_PASSWORD`. El workflow de build ya tiene el paso de firma y se activa
   solo cuando esos secrets existen. Con OV la reputación se construye con el tiempo;
   con EV el desbloqueo es inmediato.
