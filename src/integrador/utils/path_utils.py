"""
Módulo de utilidades generales.

Contiene funciones de ayuda que son utilizadas en varias partes de la aplicación,
como la gestión de rutas de recursos y la visualización de diálogos de error estándar.
"""

from PyQt6.QtWidgets import QMessageBox
import traceback
import sys
import os

def resource_path(relative_path):
    """
    Obtiene la ruta absoluta a un recurso, manejando la diferencia entre
    el entorno de desarrollo y un ejecutable de PyInstaller.

    - En un ejecutable de PyInstaller, los recursos se encuentran en una carpeta
      temporal cuya ruta se almacena en `sys._MEIPASS`.
    - En desarrollo, calcula la ruta subiendo desde la ubicación de este archivo
      hasta la raíz del proyecto.

    Args:
        relative_path (str): La ruta relativa al recurso desde la raíz del proyecto
                             (ej. "resources/ui/FormularioLogin.ui").

    Returns:
        str: La ruta absoluta y multiplataforma al recurso.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    return os.path.join(base_path, relative_path)

def show_error_message(title, message, detailed_text=""):
    """
    Muestra una ventana emergente de error estándar y modal usando PyQt6.

    Args:
        title (str): El título de la ventana de error.
        message (str): El mensaje principal y legible para el usuario.
        detailed_text (str, optional): Texto técnico detallado (como un traceback). 
                                      Se mostrará en un área expandible.
    """
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    if detailed_text:
        msg_box.setDetailedText(detailed_text)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()
