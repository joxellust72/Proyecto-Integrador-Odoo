import os
from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap
# --- CONSTRUCCIÓN DE RUTAS ABSOLUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTIFICATION_UI = os.path.join(BASE_DIR, "Notificacion.ui")

class Notification(QDialog):
    """
    Una ventana de diálogo personalizada para mostrar notificaciones de éxito.
    Se cierra automáticamente después de un tiempo determinado.
    """
    def __init__(self, title, message, duration=3200, parent=None):
        """
        Inicializa la notificación.

        Args:
            title (str): El título de la ventana.
            message (str): El mensaje a mostrar.
            duration (int): Duración en ms antes de cerrar automáticamente.
            parent: El widget padre.
        """
        super().__init__(parent)
        loadUi(NOTIFICATION_UI, self)

        # --- Estilo para bordes redondeados y sin marco ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle(title)
        self.lblMessage.setText(message)