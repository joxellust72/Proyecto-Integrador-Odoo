"""
Módulo que define un widget de notificación de éxito personalizado.
"""

import os
from PyQt6.QtWidgets import QDialog
from PyQt6.uic import loadUi
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap

from integrador.utils.path_utils import resource_path
NOTIFICATION_UI = resource_path("resources/ui/Notificacion.ui")

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
            message (str): El mensaje que se mostrará en la notificación.
            duration (int): Duración en milisegundos antes de que la ventana se cierre sola.
            parent: El widget padre sobre el cual se centrará la notificación.
        """
        super().__init__(parent)
        loadUi(NOTIFICATION_UI, self)

        # Estilo para bordes redondeados y sin marco de ventana.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle(title)
        self.lblMessage.setText(message)
        self.duration = duration

    def center_on_parent(self):
        """
        Calcula la posición para centrar este diálogo sobre su widget padre.
        Usa coordenadas globales para un centrado preciso.
        """
        if self.parent():
            # Obtiene el punto central del padre y lo mapea a coordenadas globales.
            parent_center_global = self.parent().mapToGlobal(self.parent().rect().center())
            # Calcula la posición superior-izquierda para que el centro de este diálogo se alinee.
            dialog_top_left = parent_center_global - self.rect().center()
            self.move(dialog_top_left)

    def show_centered(self):
        """
        Muestra el diálogo, lo centra sobre su padre y programa su cierre automático.
        """
        self.show()
        self.center_on_parent()
        QTimer.singleShot(self.duration, self.accept)