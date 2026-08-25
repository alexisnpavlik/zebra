"""Empaqueta la app de Brother en un ejecutable standalone con PyInstaller.

Uso:
    python build.py

El ejecutable queda en dist/BrotherQL800LabelPrinter  (Linux/Mac)
                  o  dist/BrotherQL800LabelPrinter.exe (Windows)
"""

import os
import subprocess
import sys


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "BrotherQL800LabelPrinter",
        "--add-data", f"{os.path.join(script_dir, 'assets')}:assets",
        "--collect-all", "customtkinter",
        "--collect-all", "fitz",
        "--collect-all", "barcode",
        os.path.join(script_dir, "main.py"),
    ]

    print("Construyendo ejecutable Brother...")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=script_dir)
    print("\nListo. El ejecutable está en la carpeta dist/")


if __name__ == "__main__":
    main()
