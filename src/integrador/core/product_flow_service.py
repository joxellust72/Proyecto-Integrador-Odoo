"""
Módulo de servicio para el flujo de creación de productos.

Encapsula la lógica de negocio para generar un nuevo código de producto,
crear el producto en Odoo y actualizar las propiedades correspondientes
en el documento de Inventor.
"""
import random
import os
import base64
from integrador.utils.path_utils import resource_path

class ProductFlowService:
    """Gestiona la lógica de creación de un nuevo producto."""

    def __init__(self, odoo_api, inventor_api, main_window, group_window):
        """
        Inicializa el servicio de flujo de producto.

        Args:
            odoo_api (OdooApi): Instancia de la API de Odoo.
            inventor_api (InventorApi): Instancia de la API de Inventor.
            main_window: Referencia a la ventana principal de la UI.
            group_window: Referencia a la ventana de selección de grupo.
        """
        self.odoo_api = odoo_api
        self.inventor_api = inventor_api
        self.main_window = main_window
        self.group_window = group_window

    def generate_unique_code(self):
        """
        Genera un código de producto único basado en el grupo seleccionado.

        Returns:
            str or None: Un código de 13 dígitos único, o None si falla.
        """
        group = self.group_window.property("selected_group")
        group_map = {
            "MATERIA PRIMA ENSAMBLE": "600",
            "PRE-ENSAMBLES": "650",
            "MATERIA PRIMA PROCESADA": "730"
        }
        group_num = group_map.get(group)

        if not group_num:
            self.group_window.lblMensaje.setText("Selecciona el grupo")
            return None

        while True:
            rand = random.randrange(1, 9999999999)
            numero_aleatorio_formateado = "{:010d}".format(rand)
            new_code = group_num + numero_aleatorio_formateado
            
            if not self.odoo_api.find_product_by_barcode(new_code):
                self.group_window.lblMensaje.setText("Código único generado con éxito.")
                return new_code

    def create_product_in_odoo(self):
        """
        Crea un nuevo producto en Odoo con los datos del formulario.

        Returns:
            int or None: El ID del producto creado, o None si falla.
        """
        new_code = self.main_window.txtCodigo.text()
        group = self.group_window.property("selected_group")
        
        # Mapeo de grupo a propiedades de Odoo
        group_props = {
            "MATERIA PRIMA ENSAMBLE": {'tipoInven': '3', 'estaproce': True, 'categ': 8, 'route': 43},
            "PRE-ENSAMBLES": {'tipoInven': '19', 'estaproce': False, 'categ': 9, 'route': 42},
            "MATERIA PRIMA PROCESADA": {'tipoInven': '19', 'estaproce': False, 'categ': 11, 'route': 42}
        }.get(group, {})

        image_path = resource_path(os.path.join("resources", "images", "temp_preview.png"))
        imagen_b64 = ""
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    imagen_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                os.remove(image_path)
        except Exception as img_err:
            print(f"ADVERTENCIA: No se pudo procesar la imagen. {img_err}")

        new_product_data = {
            'name': self.main_window.txtNombreSis.text(),
            'barcode': new_code,
            'image_1920': imagen_b64,
            'detailed_type': 'product',
            'list_price': 0,
            'uom_id': 1,
            'uom_po_id': 1,
            'standard_price': 0,
            'sale_ok': True,
            'purchase_ok': group_props.get('estaproce', False),
            'categ_id': group_props.get('categ'),
            'weight': self.main_window.txtMasa.text(),
            'volume': self.main_window.txtVolume.text(),
            'x_material': self.main_window.txtMaterial.text(),
            'x_Tipo_Inventario': group_props.get('tipoInven'),
            # Se asigna el ID de la subpartida arancelaria.
            # Este valor fue verificado en Odoo y corresponde a la subpartida deseada.
            'x_subpartida': 9714,
            'description_pickingout': new_code,
            'x_categoria_3': self.main_window.property("selected_category_id"),
            'x_acabado': self.main_window.txtAcabado.text(),
            'x_descripcion': self.main_window.txtDescripcion.text(),
            'x_subject': self.main_window.txtAlmacena.text(),
            'x_palabras_claves': self.main_window.textPalabraClave.toPlainText(),
            'x_docPath': self.inventor_api.doc.FullFileName if self.inventor_api.doc else "",
            'responsible_id': 2
        }

        new_product_id = self.odoo_api.create_product(new_product_data)
        if new_product_id:
            print(f"INFO: Nuevo producto creado en Odoo con ID: {new_product_id}")
            self.main_window.lblMens1.setText(f"Producto creado en Odoo con ID: {new_product_id}")
        return new_product_id

    def update_inventor_properties(self, new_product_id, designer_name, user_email):
        """
        Actualiza las iProperties del documento activo de Inventor.

        Args:
            new_product_id (int): El ID del producto de Odoo.
            designer_name (str): El nombre completo del diseñador.
            user_email (str): El email del usuario.
        """
        new_code = self.main_window.txtCodigo.text()
        properties_to_update = {
            "part_number": new_code,
            "category": self.main_window.txtCategoria.text().lower(),
            "designer": designer_name,
            "stock_number": new_product_id,
            "author": user_email,
            "keywords": self.main_window.textPalabraClave.toPlainText(),
            "clase_1": self.main_window.txtCat1.text(),
            "clase_2": self.main_window.txtCat2.text(),
            "clase_3": self.main_window.txtCat3.text()
        }

        self.inventor_api.update_document_properties(properties_to_update)
        self.inventor_api.save_document()

        self.main_window.lblMensaje.setText(f"No. de pieza actualizado en Inventor: {new_code}")
        self.main_window.lblMensaje_5.setText("Propiedades actualizadas en Inventor.")