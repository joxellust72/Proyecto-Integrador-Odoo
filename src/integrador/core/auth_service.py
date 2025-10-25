"""
Módulo del servicio de autenticación.

Encapsula la lógica para iniciar sesión en Odoo, gestionar la sesión del usuario
y manejar el archivo de configuración de credenciales.
"""
import os
import json
from integrador.api.odoo_api import OdooApi

APP_DATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'IntegradorOdooInventor')
CONFIG_FILE = os.path.join(APP_DATA_PATH, "config.json")

class AuthService:
    """Gestiona la autenticación y la sesión del usuario."""

    def __init__(self, url, db):
        """
        Inicializa el servicio de autenticación.

        Args:
            url (str): La URL del servidor Odoo.
            db (str): El nombre de la base de datos de Odoo.
        """
        self.url = url
        self.db = db
        self.odoo_api = None

    def login(self, username, password):
        """
        Intenta autenticar a un usuario contra Odoo.

        Args:
            username (str): El correo electrónico del usuario.
            password (str): La contraseña del usuario.

        Returns:
            OdooApi or None: Una instancia de OdooApi si la autenticación es exitosa,
                             de lo contrario None.
        """
        self.odoo_api = OdooApi(self.url, self.db, username, password)
        if self.odoo_api.connect():
            self._save_session(username, password)
            return self.odoo_api
        
        # Si la conexión falla, borramos cualquier sesión guardada previamente.
        self.logout()
        self.odoo_api = None
        return None

    def logout(self):
        """Cierra la sesión del usuario y elimina el archivo de configuración."""
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        self.odoo_api = None
        print("INFO: Sesión cerrada y archivo de configuración eliminado.")

    def _save_session(self, username, password):
        """Guarda las credenciales del usuario en el archivo de configuración."""
        try:
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'last_user': username, 'last_pass': password}, f)
            print("INFO: Sesión de usuario guardada en config.json.")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo guardar el archivo de sesión: {e}")

    def load_session(self):
        """
        Carga las credenciales de la última sesión desde el archivo de configuración.

        Returns:
            dict or None: Un diccionario con 'last_user' y 'last_pass' si se encuentra,
                          de lo contrario None.
        """
        if not os.path.exists(CONFIG_FILE):
            return None
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"ADVERTENCIA: No se pudo cargar la configuración de sesión: {e}")
            return None