"""
Módulo para la ventana de gestión de la Lista de Materiales (BoM).

Esta ventana se encarga de leer la estructura de un ensamblaje en Autodesk Inventor,
validar que todos sus componentes cumplan con los requisitos, y luego crear o
actualizar la BoM correspondiente en Odoo.
"""

import win32com.client as wc
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.uic import loadUi

from integrador.utils.path_utils import resource_path

UdM = {  # Unidades de medida de longitud válidas entre Inventor y Odoo.
    "mm": 6,
    "cm": 8,
    "in": 17,
    "pie": 18,
    "yd": 19,
    "m": 5,
    "km": 7,
    "mi": 20
}

class BomWindow:
    """
    Controla la lógica y la interfaz de usuario para la carga de la Lista de Materiales.
    """
    def __init__(self, inventor_instance, q_app, product_id, odoo_api_instance, unit_service_instance):
        """
        Inicializa la ventana de la BoM.

        Args:
            inventor_instance: Instancia de la aplicación de Inventor.
            q_app: Instancia de QApplication.
            product_id (int): El ID del producto de Odoo (ensamble padre) para el cual se cargará la BoM.
            odoo_api_instance (OdooApi): Instancia de la API de Odoo.
            unit_service_instance (UnitService): Instancia del servicio de unidades.
        """
        self.inv = inventor_instance
        self.app = q_app
        self.product_template_id = product_id
        self.odoo_api = odoo_api_instance
        self.unit_service = unit_service_instance

        FORM_LISTA_MATERIALES_UI = resource_path("resources/ui/FormularioListaMateriales.ui")
        self.window = loadUi(FORM_LISTA_MATERIALES_UI)

    def run(self):
        """Muestra la ventana y conecta las señales."""
        self.window.lblMensaje.setText("Estamos listos para cargar tu lista de Materiales")
        self.window.btnSubirLista.clicked.connect(self.handle_submit)
        self.window.btnNoSubirLista.clicked.connect(self.close_window)
        self.window.show()

    def close_window(self):
        """Cierra la ventana actual y la aplicación."""
        self.window.close()
        if self.app:
            self.app.quit()

    def _get_property(self, properties, set_name, prop_name):
        """
        Obtiene de forma segura una iProperty de un conjunto de propiedades de Inventor.

        Args:
            properties: El objeto PropertySets del documento de Inventor.
            set_name (str): El nombre del conjunto de propiedades (ej. "Design Tracking Properties").
            prop_name (str): El nombre de la propiedad.
        """
        try:
            prop_set = properties.Item(set_name)
            return prop_set.Item(prop_name).Value
        except Exception:
            return ""

    def _validate_material_exists(self, name: str) -> bool:
        """
        Verifica si un producto existe en Odoo buscando por su nombre.

        Args:
            name (str): El nombre del producto a buscar.

        Returns:
            bool: True si el producto existe, False en caso contrario.
        """
        if not self.odoo_api:
            return False
        producto = self.odoo_api.execute_kw('product.product', 'search', [[('name', 'ilike', name)]])
        return True if producto else False

    def _validate_code_exists(self, code: str) -> bool:
        """
        Verifica si un producto existe en Odoo buscando por su código de barras.

        Args:
            code (str): El código de barras del producto.

        Returns:
            bool: True si el producto existe, False en caso contrario.
        """
        if not self.odoo_api:
            return False
        producto = self.odoo_api.execute_kw('product.product', 'search', [[('barcode', '=', code)]])
        return True if producto else False

    def _validate_uom(self, document: wc.CDispatch):
        """
        Valida la consistencia de la unidad de medida (UoM) de un componente.
        Verifica que las propiedades físicas (masa, longitud) estén actualizadas si es necesario.
        """
        if not self.odoo_api:
            return False

        id_uni_med_data = self.odoo_api.execute_kw('product.product', 'search_read', [[('name', 'ilike', document.Document.PropertySets.Item(4).Item("Material Base").Value)]], {'fields': ['uom_id']})
        if not id_uni_med_data: return False
        
        id_uni_med = id_uni_med_data[0]['uom_id'][0]
        category_data = self.odoo_api.execute_kw('uom.uom', 'search_read', [[('id', '=', id_uni_med)]], {'fields': ['category_id']})
        if not category_data: return False

        category_id, category_name = category_data[0]['category_id']

        match category_id:
            case 1:  # Unit
                return True
            case 2:  # Weight
                if document.Document.PropertySets.Item(3).Item('Mass').Value == 0:
                    msg = f"Actualice las propiedades fisicas del producto {document.Document.PropertySets.Item(3).Item('Part Number').Value}"
                    print(msg)
                    self.window.lblMensaje.setText(msg)
                    return False
            case 4:  # Length
                if document.BOMQuantity.BaseUnits not in UdM:
                    msg = f"el componente ({document.Document.PropertySets.Item(3).Item('Part Number').Value}) contiene una unidad de medida invalida ({document.BOMQuantity.BaseUnits})"
                    print(msg)
                    self.window.lblMensaje.setText(msg)
                    return False
            case _:
                msg = f"El producto ({document.Document.PropertySets.Item(3).Item('Part Number').Value}) tiene como material Base ({document.Document.PropertySets.Item(4).Item('Material Base').Value}) el cual tiene una unidad de medida incorrecta ({category_name})"
                print(msg)
                self.window.lblMensaje.setText(msg)
                return False
        return True

    def _validate_parameters(self, component: wc.CDispatch):
        """
        Valida que un componente de Inventor tenga todas las iProperties requeridas.

        Args:
            component: El objeto ComponentDefinition del componente de Inventor.

        Returns:
            bool: True si todas las validaciones pasan, False si alguna falla.
        """
        parametros = component.Document.PropertySets
        try:
            part_number = self._get_property(parametros, "Design Tracking Properties", "part number")
            if not self._validate_code_exists(part_number):
                msg = f"El producto ({part_number}) no existe en el maestro de productos"
                print(msg)
                self.window.lblMensaje.setText(msg)
                return False

            grupo = part_number[:3]
            if not (grupo and grupo.isdigit() and len(grupo) == 3):
                print(f"El grupo del producto ({part_number}) es inválido.")
                return False

            if grupo != '650':
                for prop in ["Material", "Appearance"]:
                    if not self._get_property(parametros, "Design Tracking Properties", prop):
                        msg = f"El producto ({part_number}) no cuenta con un {prop}"
                        print(msg)
                        self.window.lblMensaje.setText(msg)
                        return False

            if grupo == '730':
                material_base_value = self._get_property(parametros, "User Defined Properties", "Material Base")
                if not material_base_value:
                    msg = f"El producto ({part_number}) no cuenta con un Material Base"
                    print(msg)
                    self.window.lblMensaje.setText(msg)
                    return False
                elif not self._validate_material_exists(material_base_value):
                    msg = f"El Material Base del producto ({part_number}) no existe en el maestro de productos"
                    print(msg)
                    self.window.lblMensaje.setText(msg)
                    return False
                elif not self._validate_uom(component):
                    return False

            required_props = {'Mass': 3, 'Part Number': 3, 'description': 3, 'Title': 1, 'subject': 1, 'Clase 1': 4, 'Clase 2': 4, 'Clase 3': 4}
            for prop, item_idx in required_props.items():
                if not parametros.Item(item_idx).Item(prop).Value:
                    msg = f"El producto ({part_number}) no cuenta con un {prop}"
                    print(msg)
                    self.window.lblMensaje.setText(msg)
                    return False

        except wc.pywintypes.com_error as e:
            msg = f"Error de parámetro en el producto ({part_number}): {e}"
            print(msg)
            self.window.lblMensaje.setText(msg)
            return False

        return True

    def _recursive_validation(self, elemento: wc.CDispatch, padre: str, nivel: int = 0):
        """
        Recorre recursivamente la BoM de Inventor y valida cada componente.

        Args:
            elemento: La colección de filas de la BoM (BOMRows).
            padre (str): El número de pieza del componente padre.
            nivel (int): El nivel de profundidad actual en la recursión (para indentación).

        Returns:
            bool: True si toda la rama es válida, False si se encuentra un error.
        """
        for objeto in elemento:
            parte = objeto.ComponentDefinitions(1)
            atributos = parte.Document.PropertySets
            part_number = atributos.Item(3).Item("part number").value

            if self._validate_parameters(parte):
                msg = (nivel * "    ") + padre + " -> " + part_number + " -> " + str(objeto.ItemQuantity)
                print(msg)
                self.window.lblMensaje.setText(msg)

                if part_number.startswith('730'):
                    # Lógica de impresión para 730...
                    pass

                if objeto.ChildRows is not None:
                    if not self._recursive_validation(objeto.ChildRows, part_number, (nivel + 1)):
                        return False
            else:
                return False
        return True

    def _clear_and_get_bom_id(self, product_code: str) -> str:
        """
        Obtiene el ID de la BoM para un producto. Si la BoM ya existe, borra sus líneas.
        Si no existe, crea una nueva BoM.

        Args:
            product_code (str): El código de barras del producto plantilla.

        Returns:
            str: El ID de la BoM (nueva o existente).
        """
        if not self.odoo_api: return ""

        product_tmp_ids = self.odoo_api.execute_kw('product.template', 'search', [[('barcode', '=', product_code)]], {'limit': 1})
        if not product_tmp_ids: return ""
        product_tmp_id = product_tmp_ids[0]

        bom_ids = self.odoo_api.execute_kw('mrp.bom', 'search', [[('product_tmpl_id', '=', product_tmp_id)]], {'limit': 1})

        if bom_ids:
            bom_id = bom_ids[0]
            bom_line_ids = self.odoo_api.execute_kw('mrp.bom.line', 'search', [[['bom_id', '=', bom_id]]])
            if bom_line_ids:
                self.odoo_api.execute_kw('mrp.bom.line', 'unlink', [bom_line_ids])
        else:
            bom_data = [{'consumption': 'flexible', 'product_tmpl_id': product_tmp_id, 'product_qty': 1}]
            new_bom_id = self.odoo_api.execute_kw('mrp.bom', 'create', [bom_data])
            bom_id = new_bom_id[0] if isinstance(new_bom_id, list) else new_bom_id

        return bom_id

    def _recursive_bom_creation(self, elemento: wc.CDispatch, bom_id: str):
        """
        Recorre recursivamente la BoM de Inventor y crea las líneas de BoM en Odoo.

        Args:
            elemento: La colección de filas de la BoM (BOMRows).
            bom_id (str): El ID de la BoM padre en Odoo a la que se añadirán las líneas.
        """
        if not self.odoo_api: return

        for objeto in elemento:
            codigo_sizfra_props = objeto.ComponentDefinitions(1).Document.PropertySets
            part_number = codigo_sizfra_props(3).Item('part number').value
            product_ids = self.odoo_api.execute_kw('product.product', 'search', [[('barcode', '=', part_number)]], {'limit': 1})
            if not product_ids: continue
            product_id = product_ids[0]

            cantidad = objeto.ItemQuantity
            vals = [{'bom_id': bom_id, 'product_id': product_id, 'product_qty': cantidad}]
            self.odoo_api.execute_kw('mrp.bom.line', 'create', [vals])

            if objeto.ChildRows is not None:
                child_bom_id = self._clear_and_get_bom_id(part_number)
                self._recursive_bom_creation(objeto.ChildRows, child_bom_id)

            if part_number.startswith('730'):
                # Lógica de creación de línea para 730...
                pass

    def handle_submit(self):
        """
        Manejador para el botón 'Subir Lista'.
        Orquesta todo el proceso: validación y posterior creación de la BoM en Odoo.
        """
        self.window.lblMensaje.setText("Subiendo tus datos al sistema de información...")
        self.app.processEvents()

        ensamble = self.inv.ActiveDocument
        part_number = ensamble.ComponentDefinitions(1).Document.PropertySets(3).Item("part number").value

        if self._validate_parameters(ensamble.ComponentDefinitions(1)) and \
           self._recursive_validation(ensamble.ComponentDefinition.BOM.BOMViews.Item(2).BOMRows, part_number, 0):
            
            bom_id = self._clear_and_get_bom_id(part_number)
            bom_rows = ensamble.ComponentDefinition.BOM.BOMViews(2).BOMRows
            self._recursive_bom_creation(bom_rows, bom_id)
            self.window.lblMensaje.setText("Hemos cargado tu lista de materiales exitosamente")
        else:
            print("Error en la validación.")
            # El mensaje de error específico ya se estableció en los métodos de validación.

def run_lista_materiales(inventor_instance, q_application, product_id, odoo_api, unit_service):
    """
    Punto de entrada para crear y ejecutar la ventana de la Lista de Materiales.

    Args:
        inventor_instance: Instancia de la aplicación de Inventor.
        q_application: Instancia de QApplication.
        product_id (int): ID del producto padre en Odoo.
        odoo_api (OdooApi): Instancia conectada de la API de Odoo.
        unit_service (UnitService): Instancia del servicio de unidades.
    """
    if not odoo_api or not unit_service:
        QMessageBox.critical(
            None, 
            "Error de Inicialización", 
            "No se pudo inicializar la ventana de Lista de Materiales.\n"
            "Faltan las instancias de la API de Odoo o del Servicio de Unidades.",
        )
        return

    bom_app = BomWindow(inventor_instance, q_application, product_id, odoo_api, unit_service)
    bom_app.run()
