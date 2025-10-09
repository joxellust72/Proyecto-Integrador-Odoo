"""
Módulo de la API para interactuar con Odoo.

Esta clase encapsula la lógica de conexión y comunicación con un servidor Odoo
a través de XML-RPC. Proporciona métodos para autenticar, ejecutar comandos
y realizar operaciones específicas del modelo de producto.
"""
import xmlrpc.client

class OdooApi:
    """Una clase para interactuar con la API de Odoo a través de XML-RPC."""

    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None

    def connect(self):
        """
        Establece conexión con el servidor Odoo y autentica al usuario.

        Returns:
            bool: True si la conexión y autenticación fueron exitosas,
                  False en caso contrario.
        """
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                print(f"INFO: Conexión exitosa a Odoo para el usuario '{self.username}' (UID: {self.uid}).")
                return True
            print(f"ERROR: Fallo de autenticación en Odoo para el usuario '{self.username}'.")
            return False
        except Exception as e:
            print(f"ERROR: No se pudo conectar a Odoo en {self.url}. Error: {e}")
            self.uid = None
            self.models = None
            return False

    def get_connection_info(self):
        """
        Devuelve un diccionario con la información de la conexión actual.

        Returns:
            dict: Un diccionario con los detalles de la sesión activa.
        """
        return {
            'uid': self.uid,
            'current_user_email': self.username
        }

    def execute_kw(self, model, method, args, kwargs=None):
        """
        Ejecuta un método en un modelo de Odoo con manejo de errores.
        """
        if kwargs is None:
            kwargs = {}
        if not self.models:
            print("ERROR: No hay conexión a Odoo para ejecutar el método.")
            return None
        try:
            return self.models.execute_kw(self.db, self.uid, self.password, model, method, args, kwargs or {})
        except Exception as e:
            print(f"Error al ejecutar {model}.{method}: {e}")
            return None

    def create_product(self, product_data):
        """
        Crea un nuevo producto en Odoo.

        Args:
            product_data (dict): Un diccionario con los valores para el nuevo producto.

        Returns:
            int or None: El ID del producto recién creado si tiene éxito, de lo contrario None.
        """
        new_product_id = self.execute_kw('product.product', 'create', [product_data])
        return new_product_id if new_product_id else None

    def find_product_by_barcode(self, barcode):
        """
        Busca un producto en Odoo por su código de barras o referencia interna.

        Args:
            barcode (str): El código a buscar.

        Returns:
            int or None: El ID del producto si se encuentra uno, de lo contrario None.
        """
        search_domain = ['|', ['default_code', '=', barcode], ['barcode', '=', barcode]]
        product_ids = self.execute_kw('product.product', 'search', [search_domain], {'limit': 1})
        return product_ids[0] if product_ids else None