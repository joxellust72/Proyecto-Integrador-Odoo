"""
Módulo que define un widget de notificación de error modal y personalizado.
"""
import os
from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from integrador.utils.path_utils import resource_path

# Rutas a los recursos de la UI.
ERROR_NOTIFICATION_UI = resource_path("resources/ui/ErrorNotification.ui")

class ErrorNotification(QDialog):
    """
    Una ventana de diálogo personalizada para mostrar notificaciones de error.

    A diferencia de la notificación de éxito, esta es modal y requiere que el
    usuario interactúe (presione 'Aceptar') para cerrarla.
    """
    def __init__(self, title, message, parent=None):
        """
        Inicializa la notificación de error.

        Args:
            title (str): El título de la ventana.
            message (str): El mensaje que se mostrará en la notificación.
            parent: El widget padre sobre el cual se centrará la notificación.
        """
        super().__init__(parent)
        loadUi(ERROR_NOTIFICATION_UI, self)

        # Configuración de la apariencia de la ventana.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.lblTitle.setText(title)
        self.lblMessage.setText(message)

        self.btnAceptar.clicked.connect(self.accept)

    def center_on_parent(self):
        """Calcula la posición para centrar este diálogo sobre su widget padre."""
        if self.parent():
            parent_center_global = self.parent().mapToGlobal(self.parent().rect().center())
            dialog_top_left = parent_center_global - self.rect().center()
            self.move(dialog_top_left)

    def show_centered(self):
        """
        Muestra el diálogo, lo centra sobre su padre y lo ejecuta de forma modal.
        El modo modal bloquea la interacción con la ventana principal hasta que
        este diálogo se cierra.
        """
        self.center_on_parent()
        self.exec()