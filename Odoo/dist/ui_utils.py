from PyQt6.QtWidgets import QMessageBox
import traceback

def show_error_message(title, message, detailed_text=""):
    """
    Muestra una ventana emergente de error estándar usando PyQt6.

    Args:
        title (str): El título de la ventana de error.
        message (str): El mensaje principal y simple para el usuario.
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
