"""
Punto de entrada de ciphercoin.

Ejecutar directamente:
    python main.py
"""

import sys
import os

# aseguramos que src/ esté en el path para importaciones relativas
_SRC = os.path.join(os.path.dirname(__file__), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from ciphercoin.gui import main

if __name__ == "__main__":
    main()
