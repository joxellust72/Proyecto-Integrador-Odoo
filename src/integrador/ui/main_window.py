import random
import sys
import os
import json
import base64
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QLineEdit, QMessageBox, QCompleter
from PyQt6.uic import loadUi

# Importamos la función de ayuda desde el módulo de utilidades
from integrador.utils.path_utils import show_error_message, resource_path
from integrador.api.odoo_api import OdooApi
from integrador.api.inventor_api import InventorApi
from integrador.core.unit_service import UnitService
from integrador.ui.components.notification import Notification
from integrador.ui.components.error_notification import ErrorNotification
from integrador.core import user_service

# Rutas a los archivos de la interfaz de usuario
FORM_LOGIN_UI = resource_path("resources/ui/FormularioLogin.ui")
FORM_GRUPO_UI = resource_path("resources/ui/FormularioGrupo.ui")
FORM_ODOO_UI = resource_path("resources/ui/FormularioOdoo.ui")

APP_DATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'IntegradorOdooInventor') # Carpeta para datos de la app
os.makedirs(APP_DATA_PATH, exist_ok=True) # Creamos la carpeta si no existe
CONFIG_FILE = os.path.join(APP_DATA_PATH, "config.json")
class MainApplication:
    """
    Clase principal que gestiona el estado y el flujo de la aplicación.
    """
    def __init__(self, inventor_instance, q_app):
        """
        Inicializa la aplicación principal.

        Args:
            inventor_instance: Una instancia de la aplicación de Inventor (real o simulada).
            q_app: La instancia de QApplication.
        """
        # Inicialización de estado y servicios
        self.app = q_app
        self.inv = inventor_instance
        self.inventor_api = InventorApi(self.inv, self.app)
        
        # Servicios que se inicializarán después del login
        self.odoo_api = None
        self.unit_service = None
        self.odoo_connection_info = {}
        self.categorias_3 = []
        
        # Propiedades para almacenar temporalmente los datos del material base
        self._current_base_material_qty = 0.0
        self._current_base_material_unit = ""

        # Constantes de conexión
        self.URL_ODOO = 'http://192.168.10.13:8069'
        self.DB_ODOO = 'PruebaCFReA'

        # Carga de interfaces de usuario
        self.login_window = uic.loadUi(FORM_LOGIN_UI)
        self.group_window = uic.loadUi(FORM_GRUPO_UI)
        self.main_window = uic.loadUi(FORM_ODOO_UI)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Configuración inicial de los elementos de la UI."""
        self.main_window.lblMensaje_5.setText("Autodesk Inventor tiene un documento activo.")
        self.main_window.ComboBoxDescripcion.clear()
        self.main_window.groupBox_MaterialBase.setVisible(False)
        self.main_window.btn650.setEnabled(False)
        self.main_window.btn730.setEnabled(True)

    def _connect_signals(self):
        """Conecta todos los eventos de la UI (clics de botón, etc.) a sus métodos manejadores."""
        # Ventana de Login
        self.login_window.btnIniciarSesion.clicked.connect(self.handle_login)
        self.login_window.btnMostrarClave.clicked.connect(self.toggle_password_visibility)
        self.login_window.btnCerrarApp.clicked.connect(self.quit_app)

        # Ventana de Grupo
        self.group_window.btnGrupoMateriaPrimaEnsamble.clicked.connect(self.handle_group_selection)
        self.group_window.btnGrupoPreEnsambles.clicked.connect(self.handle_group_selection)
        self.group_window.btnGrupoMateriaPrimaProcesada.clicked.connect(self.handle_group_selection)
        self.group_window.btnCerrarSesion.clicked.connect(self.handle_logout)

        # Ventana Principal
        self.main_window.btnAbrirFormularioGrupo.clicked.connect(self.show_group_window)
        self.main_window.btnValidar.clicked.connect(self.handle_validate)
        self.main_window.btnEnviar.clicked.connect(lambda: self.handle_submit(self.main_window.txtCodigo.text()))
        self.main_window.btnCerrarPrin.clicked.connect(self.quit_app)
        
        # Flujos secundarios
        self.main_window.btn650.clicked.connect(self.open_bom_window)
        self.main_window.btn730.clicked.connect(self.handle_existing_part_730)
        self.main_window.btnMostrarMaterialBase.clicked.connect(self.show_material_base_section)
        
        # Sección de material base integrado
        self.main_window.btnValidar_integrado.clicked.connect(self.handle_validate_base_material_quantity)
        self.main_window.btnCargar_integrado.clicked.connect(self.handle_create_bom_for_product)

    def run(self):
        """Inicia la aplicación mostrando la ventana de login."""
        self.login_window.show()
        self.load_session_config()

    def quit_app(self):
        """Cierra la aplicación."""
        if self.app:
            self.app.quit()

    def post_login_setup(self):
        """Tareas a ejecutar después de un inicio de sesión exitoso."""
        self.unit_service = UnitService(self.odoo_api)
        self.categorias_3 = self._get_category_descriptions()
        if self.categorias_3:
            self.categorias_3.sort(key=lambda cat: cat.get('x_name', ''))
        self._populate_category_combobox()

    def show_group_window(self):
        """Muestra la ventana de selección de grupo."""
        self.login_window.close()
        self.main_window.close()
        
        if "MockApplication" in self.inv.__class__.__name__ and not self.inventor_api.doc:
            self.inventor_api.doc = self.inv.CreateNewDocument()
            print(f"INFO: Nuevo documento simulado '{self.inventor_api.doc.Name}' está activo.")
        
        # Usamos un QTimer para retrasar el ajuste de la vista. Esto da tiempo a la
        # ventana de Inventor a estar completamente lista y enfocada, evitando errores de COM.
        # El ajuste se ejecutará 200ms después de que esta función termine.
        QTimer.singleShot(200, self.inventor_api.set_isometric_view)
        
        self.group_window.show()

    def get_material_base_from_inventor(self, product_id):
        """
        Lee la iProperty 'Codigo Sizfra' de Inventor, busca el producto en Odoo
        y actualiza el formulario integrado.
        """
        try:
            codigo_sizfra = self.inventor_api._get_property("User Defined Properties", "CODIGO SIZFRA")

            if not codigo_sizfra:
                QMessageBox.critical(self.main_window, "Error", "La iProperty 'Codigo Sizfra' no puede estar vacía en el documento de Inventor.")
                return False

            codigo_sizfra = str(int(float(codigo_sizfra))).strip()
            search_domain = ['|', ['default_code', '=', codigo_sizfra], ['barcode', '=', codigo_sizfra]]
            product_ids = self.odoo_api.execute_kw('product.product', 'search_read', [search_domain], {'fields': ['id', 'name', 'default_code'], 'limit': 1})

            if not product_ids:
                error_msg = f"No se encontró material base en Odoo con el código '{codigo_sizfra}' (ni como Ref. Interna ni como Cód. Barras)."
                QMessageBox.critical(self.main_window, "Error de Búsqueda", error_msg)
                return False

            product_name = product_ids[0]['name']
            found_code = product_ids[0].get('default_code') or codigo_sizfra
            self.main_window.txtMaterialBase_integrado.setText(found_code)
            self.main_window.lblMensaje_3.setText(f"Material base '{product_name}' (código: {found_code}) cargado.")
            return True

        except Exception as e:
            error_msg = f"No se pudo leer la propiedad 'Codigo Sizfra' de Inventor. Asegúrese de que exista. Error: {e}"
            print(f"ERROR: {error_msg}")
            QMessageBox.critical(self.main_window, "Error de Inventor", error_msg)
            return False

    def get_base_material_id(self):
        """
        Obtiene el ID del producto en Odoo correspondiente al material base.

        Busca el producto utilizando el código del campo 'txtMaterialBase_integrado'.

        Returns:
            int or None: El ID del producto si se encuentra, de lo contrario None.
        """
        CodigoMaterialBase = str(self.main_window.txtMaterialBase_integrado.text()).strip()
        if not self.odoo_api: return None
        search_domain = ['|', ['default_code', '=', CodigoMaterialBase], ['barcode', '=', CodigoMaterialBase]]
        search_result = self.odoo_api.execute_kw('product.product', 'search', [search_domain], {'limit': 1})
        return search_result[0] if search_result else None

    def get_base_material_uom(self):
        """
        Obtiene el nombre de la unidad de medida (UoM) del material base desde Odoo.

        Returns:
            str: El nombre de la unidad de medida (ej. "kg", "unidades"),
                 o una cadena vacía si no se puede determinar.
        """
        if not self.odoo_api: return ""
        material_base_ids_prod = self.get_base_material_id()
        if not material_base_ids_prod:
            return ""
        product_datauom = self.odoo_api.execute_kw('product.product', 'read', [material_base_ids_prod], {'fields': ['uom_id']})
        uom_id = product_datauom[0]['uom_id']
        uom_data = self.odoo_api.execute_kw('uom.uom', 'read', [uom_id[0]], {'fields': ['name']})
        return uom_data[0]['name']

    def get_base_material_quantity(self):
        """
        Determina la cantidad requerida del material base desde Inventor.

        Si la unidad de medida en Odoo es 'kg', calcula la masa.
        De lo contrario, intenta obtener la cantidad de la BoM de Inventor.

        Returns:
            tuple: Una tupla conteniendo (float: cantidad, str: unidad).
        """
        if not self.inv: return 0, ""
        uom_data1 = self.get_base_material_uom()
        uom_info_odoo = self.unit_service.get_uom_info(uom_data1)

        if not uom_info_odoo:
            QMessageBox.critical(self.main_window, "Error de Unidad", f"La unidad de medida '{uom_data1}' del material base en Odoo no es válida o no se encontró.")
            return

        uom_category_id = uom_info_odoo['category_id']

        # Categoría 2: Peso (Weight)
        if uom_category_id == 2:
            # La propiedad 'Mass' de Inventor viene en GRAMOS.
            mass_in_grams = self.inventor_api._get_property("Design Tracking Properties", "Mass", 0.0)
            self._current_base_material_qty = mass_in_grams
            self._current_base_material_unit = "g" # Siempre leemos en gramos para máxima precisión
            
            # Convertimos a la unidad de Odoo para mostrar en la UI
            display_qty = self.unit_service.convert(mass_in_grams, "g", uom_data1)
            self.main_window.txtCantReq_integrado.setText(f"{display_qty:.4f} {uom_data1}")
            self.main_window.txtCantReq_integrado.setReadOnly(True)

        # Categoría 1: Unidad (Unit) o cualquier otra categoría no manejada explícitamente
        # También entra aquí si no hay `UnitQuantity`
        elif uom_category_id == 1 or not self.inventor_api.doc.ComponentDefinition.BOMQuantity.UnitQuantity:
             # Para unidades, asumimos 1 a menos que se especifique lo contrario.
            ValueOdoo = 1
            unit_str = uom_data1 if uom_data1 else "Uni"
            self.main_window.txtCantReq_integrado.setText(f"1 {unit_str}")
            self.main_window.txtCantReq_integrado.setReadOnly(True)
            self._current_base_material_qty = 1
            self._current_base_material_unit = unit_str

        # Otras categorías (como Longitud) que usan BOMQuantity
        else:
            ValueOdooForm = self.inventor_api.doc.ComponentDefinition.BOMQuantity.UnitQuantity
            parts = ValueOdooForm.split(" ", 1)
            ValueOdoo = float(parts[0].replace(',', '.')) if parts else 0.0
            unit_str = parts[1] if len(parts) > 1 else uom_data1
            self._current_base_material_qty = ValueOdoo
            self._current_base_material_unit = unit_str
            self.main_window.txtCantReq_integrado.setText(ValueOdooForm)
            self.main_window.txtCantReq_integrado.setReadOnly(True)

    def handle_validate_base_material_quantity(self):
        """
        Manejador para el botón 'Validar' en la sección de material base.
        Calcula y almacena la cantidad y unidad del material base.
        """
        self.get_base_material_quantity()

    def handle_create_bom_for_product(self):
        """Crea o actualiza la BoM para un producto usando el material base del formulario."""
        parent_product_id = self.main_window.property("current_parent_product_id")

        if not parent_product_id:
            QMessageBox.critical(self.main_window, "Error Crítico", "No se ha podido identificar el producto padre para crear la BoM.")
            return

        # Buscamos el ID del 'product.template' a partir del ID del 'product.product'
        parent_product_data = self.odoo_api.execute_kw('product.product', 'read', [parent_product_id], {'fields': ['product_tmpl_id']})
        if not parent_product_data or not parent_product_data[0].get('product_tmpl_id'):
            QMessageBox.critical(self.main_window, "Error Crítico", f"No se pudo encontrar la plantilla de producto para el ID: {parent_product_id}.")
            return
        parent_template_id = parent_product_data[0]['product_tmpl_id'][0]

        material_base_ids_prod = self.get_base_material_id()
        if not material_base_ids_prod:
            QMessageBox.critical(self.main_window, "Error", "No se pudo encontrar el material base en Odoo. Verifique el código.")
            return

        # 1. Buscar o crear la BoM para el producto padre
        bom_ids = self.odoo_api.execute_kw('mrp.bom', 'search', [[('product_tmpl_id', '=', parent_template_id)]], {'limit': 1})
        if bom_ids:
            bom_id = bom_ids[0]
            # Opcional: podrías querer limpiar las líneas existentes si la BoM se puede regenerar
            # bom_line_ids = self.odoo_api.execute_kw('mrp.bom.line', 'search', [[['bom_id', '=', bom_id]]])
            # if bom_line_ids: self.odoo_api.execute_kw('mrp.bom.line', 'unlink', [bom_line_ids])
        else:
            vals = [{'product_tmpl_id': parent_template_id, 'product_qty': 1, 'consumption': 'flexible'}]
            new_bom_id = self.odoo_api.execute_kw('mrp.bom', 'create', [vals])
            bom_id = new_bom_id[0] if new_bom_id else None

        if not bom_id:
            QMessageBox.critical(self.main_window, "Error", "No se pudo crear o encontrar la lista de materiales para el producto padre.")
            return

        # 2. Usar la cantidad y unidad ya calculadas y almacenadas
        if self._current_base_material_qty <= 0:
            QMessageBox.warning(self.main_window, "Validación Requerida", "Por favor, presione 'Validar Cantidad' antes de cargar el material base.")
            return

        # Obtenemos la unidad de medida de destino desde Odoo para el material base
        uom_name_odoo = self.get_base_material_uom()
        uom_info_odoo = self.unit_service.get_uom_info(uom_name_odoo)

        if not uom_info_odoo:
            QMessageBox.critical(self.main_window, "Error", f"No se pudo encontrar la información de la unidad de medida '{uom_name_odoo}' en Odoo.")
            return

        uom_id = uom_info_odoo['id']
        
        # Realizamos la conversión precisa desde la unidad de Inventor a la unidad de Odoo
        cantidad_convertida = self.unit_service.convert(self._current_base_material_qty, self._current_base_material_unit, uom_name_odoo)
        print(f"INFO: Conversión de '{self._current_base_material_qty} {self._current_base_material_unit}' (Inventor) a '{cantidad_convertida:.6f} {uom_name_odoo}' (Odoo).")

        # 3. Crear la línea de la BoM
        vals = [{'bom_id': bom_id, 'product_id': material_base_ids_prod, 'product_qty': cantidad_convertida, 'product_uom_id': uom_id}]
        
        bom_line_id_creada = self.odoo_api.execute_kw('mrp.bom.line', 'create', [vals])
        
        if not bom_line_id_creada:
            QMessageBox.critical(self.main_window, "Error", "No se pudo crear la línea de la lista de materiales en Odoo.")
            return
        
        self.main_window.lblMensaje_3.setText(f"Lista de materiales actualizada con éxito. Línea ID: {bom_line_id_creada[0]}")
        self.main_window.btnCargar_integrado.setStyleSheet("background-color: blue; color: white;")
        self.main_window.btnCargar_integrado.setEnabled(False)

        notification = Notification(
            title="Éxito",
            message="El material base se ha asignado correctamente a la pieza.",
            parent=self.main_window
        )
        notification.show_centered()
        QTimer.singleShot(2000, self.quit_app)

    def _set_category_by_group(self):
        """
        Establece el campo de texto de la categoría en la ventana principal
        basándose en el grupo seleccionado en la ventana de grupos.
        """
        GrSiFor = self.group_window.property("selected_group") # Usamos la propiedad que guardamos
        if GrSiFor == "MATERIA PRIMA ENSAMBLE":       
            self.main_window.txtCategoria.setText("MATERIA PRIMA ENSAMBLE")
        elif GrSiFor == "PRE-ENSAMBLES":        
            self.main_window.txtCategoria.setText("PRE-ENSAMBLES")         
        elif GrSiFor == "MATERIA PRIMA PROCESADA":
            self.main_window.txtCategoria.setText("MATERIA PRIMA PROCESADA")
                  
    def _generate_unique_code(self):
        """
        Genera un código de producto único basado en el grupo seleccionado.

        Returns:
            str or None: Un código de 13 dígitos único si se puede generar, de lo contrario None.
        """
        GrSiFor = self.group_window.property("selected_group") # Usamos la propiedad que guardamos
        
        if GrSiFor == "MATERIA PRIMA ENSAMBLE":
            grupoNum = "600"
        elif GrSiFor == "PRE-ENSAMBLES":
            grupoNum = "650"
        elif GrSiFor == "MATERIA PRIMA PROCESADA":
            grupoNum = "730"
        else:
            self.group_window.lblMensaje.setText("Selecciona el grupo")
            return None

        while True:
            rand = random.randrange(1, 9999999999)
            numero_aleatorio_formateado = "{:010d}".format(rand)
            codigonuevo = grupoNum + numero_aleatorio_formateado
            
            # Verificamos si el código ya existe en Odoo
            if not self.odoo_api.find_product_by_barcode(codigonuevo):
                self.group_window.lblMensaje.setText("Código único generado con éxito.")
                return codigonuevo

    def _create_product_in_odoo(self, codigonuevo):
        """
        Crea un nuevo producto en Odoo con los datos del formulario.

        Args:
            codigonuevo (str): El código de barras/referencia interna para el nuevo producto.

        Returns:
            int or None: El ID del producto recién creado si la operación es exitosa,
                         de lo contrario None.
        """
        codigonuevo = self.main_window.txtCodigo.text()    
        Material = str(self.main_window.txtMaterial.text())
        Masa = str(self.main_window.txtMasa.text())
        volume = str(self.main_window.txtVolume.text())
        GrSiFor = self.group_window.property("selected_group") # Usamos la propiedad que guardamos
        nombre = self.main_window.txtNombreSis.text()
        clases = self._update_labels_from_combobox()
        acabado = self.main_window.txtAcabado.text()
        descripcion = self.main_window.txtDescripcion.text()
        subject = self.main_window.txtAlmacena.text()    
        palabclave = self.main_window.textPalabraClave.toPlainText()
        path = self.inventor_api.doc.FullFileName if self.inventor_api.doc else ""

        imagen_b64 = ""
        # La imagen ya fue creada durante la validación, solo necesitamos la ruta para leerla.
        image_path = resource_path(os.path.join("resources", "images", "temp_preview.png")) 
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    imagen_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                # Borramos la imagen después de usarla
                os.remove(image_path)
        except Exception as img_err:
            print(f"ADVERTENCIA: No se pudo generar o codificar la imagen. {img_err}")
        
        if GrSiFor == "MATERIA PRIMA ENSAMBLE":
            tipoInven = '3'  
            estaproce = True 
            categ = 8
            route = 43   
        elif GrSiFor == "PRE-ENSAMBLES":
            tipoInven = '19'
            estaproce = False
            categ = 9
            route = 42
        elif GrSiFor == "MATERIA PRIMA PROCESADA":
            tipoInven = '19'
            estaproce = False
            route = 42
            categ = 11
        
        new_product_data = {
            'name': nombre,
            'barcode': codigonuevo,
            'image_1920': imagen_b64,
            'detailed_type' : 'product',
            'list_price' : 0,
            'taxes_id' : [],
            'uom_id' : 1,
            'uom_po_id' : 1,
            'standard_price' : 0,
            'supplier_taxes_id' : [],
            'sale_ok' : True,
            'purchase_ok' : estaproce,
            'categ_id' : categ,
            'weight' : Masa,
            'volume' : volume,
            'x_material' : Material,
            'x_Tipo_Inventario': tipoInven,
            'x_subpartida': 9714,             
            'description_pickingout': codigonuevo,
            'x_categoria_3': clases,
            'x_acabado': acabado,
            'x_descripcion': descripcion, 
            'x_subject': subject,           
            'x_palabras_claves': palabclave,   
            'x_docPath': path,              
            'responsible_id' : 2
        }

        new_product_id = self.odoo_api.create_product(new_product_data)
        if new_product_id:
            print("Nuevo producto creado en el ERP Odoo con ID:", new_product_id)
            self.main_window.lblMens1.setText(f"Nuevo producto creado en el ERP Odoo con ID: {new_product_id}")
        return new_product_id
    
    def _update_inventor_properties(self, codigonuevo, designer):
        """
        Actualiza las iProperties del documento activo de Inventor.

        Args:
            codigonuevo (str): El nuevo número de pieza.
            designer (str): El nombre del diseñador/usuario actual.
        """
        codigonuevo = self.main_window.txtCodigo.text()
        cate = self.main_window.txtCategoria.text()
        cat1 = self.main_window.txtCat1.text()
        cat2 = self.main_window.txtCat2.text()
        cat3 = self.main_window.txtCat3.text()
        autor = self.odoo_connection_info.get('current_user_email', '')
        palabclave = self.main_window.textPalabraClave.toPlainText()
        product_id = self.get_product_id_from_barcode()

        properties_to_update = {
            "part_number": codigonuevo,
            "category": cate.lower(),
            "designer": designer,
            "stock_number": product_id,
            "author": autor,
            "keywords": palabclave,
            "clase_1": cat1,
            "clase_2": cat2,
            "clase_3": cat3
        }

        self.inventor_api.update_document_properties(properties_to_update)
        self.inventor_api.save_document()

        self.main_window.lblMensaje.setText(f"Se ha establecido el nuevo número de pieza en Autodesk Inventor: {codigonuevo}")
        self.main_window.lblMensaje_4.setText(f"Se ha establecido la nueva categoria de la pieza en Autodesk Inventor: {cate.lower()}")
        self.main_window.lblMensaje_5.setText(f"Se han actualizado las propiedades en Autodesk Inventor.")

    def show_main_window(self):
        """
        Configura y muestra la ventana principal de la aplicación después de
        seleccionar un grupo.
        """
        codigo = self._generate_unique_code()
        self._set_category_by_group()      
        self.main_window.txtCodigo.setText(codigo) 
        self.main_window.txtCodigo.setReadOnly(True)
        self.main_window.lblMens1.setText("Aplicativo listo para conectar con Autodesk Inventor, ERP Odoo, Sistema información Sizfra, ")
        self.main_window.show()
        self.group_window.close()

    def handle_group_selection(self):
        """Maneja el clic de cualquiera de los tres botones de grupo."""
        sender = self.app.sender()
        group_name = sender.text().split(' (')[0]
        self.group_window.setProperty("selected_group", group_name)
        self.show_main_window()

    def handle_validate(self):
        """
        Manejador para el botón 'Validar'.
        Rellena los campos del formulario con las iProperties del documento
        activo de Inventor.
        """
        print("INFO: Botón 'Validar' presionado. Rellenando campos desde Inventor.")
        
        props = self.inventor_api.get_all_properties()
        codigo_inventor = props.get("part_number")

        if codigo_inventor:
            error_dialog = ErrorNotification(
                title="Pieza Posiblemente Registrada",
                message='La pieza activa ya tiene un "No. de pieza".\n\n'
                        'Si es un nuevo producto, borre este valor en Inventor y vuelva a validar.',
                parent=self.main_window
            )
            error_dialog.show_centered()
            return

        usuario_logueado = self.odoo_connection_info.get('current_user_email', 'Desconocido')
        userlbl = user_service.get_user_full_name(usuario_logueado)

        nombre = props.get("title")
        if not nombre:
            self.main_window.lblMensaje_5.setText("No se encontró la propiedad 'Title' en el documento.")
            return

        self.main_window.txtDescripcion.setText(props.get("description"))
        self.main_window.txtAlmacena.setText(props.get("subject"))
        self.main_window.txtNombreSis.setText(nombre)
        self.main_window.txtMaterial.setText(props.get("material"))
        self.main_window.txtAcabado.setText(props.get("appearance"))
        self.main_window.txtMasa.setText(str(round(props.get("mass", 0.0) / 1000, 2)))
        self.main_window.txtCategoria.setText(props.get("category"))
        self.main_window.txtVolume.setText(str(round(props.get("volume", 0.0), 2)))
        self.main_window.textPalabraClave.setPlainText(props.get("keywords"))

        for field in [self.main_window.txtDescripcion, self.main_window.txtAlmacena, self.main_window.txtNombreSis,
                      self.main_window.txtMaterial, self.main_window.txtAcabado, self.main_window.txtMasa,
                      self.main_window.txtCategoria, self.main_window.txtVolume, self.main_window.textPalabraClave]:
            field.setReadOnly(True)

        self.main_window.lblMensaje.setText("Datos obtenidos del aplicativo Autodesk Inventor Professional.")
        self.main_window.lblMens1.setText("Bienvenido, " + userlbl)
        self.main_window.btnValidar.setStyleSheet("background-color: blue; color: white;")
        self.main_window.lblMensaje_5.setText("Código creado con éxito")

        try:
            image_path = resource_path(os.path.join("resources", "images", "temp_preview.png"))
            
            # --- INICIO DE LA CORRECCIÓN ---
            # Asegurarse de que el directorio para la imagen exista
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            # --- FIN DE LA CORRECCIÓN ---

            self.inventor_api.capture_preview_image(image_path)
            pixmap = QPixmap(image_path)
            self.main_window.lblImagen.setPixmap(pixmap)
            print(f"INFO: Previsualización de imagen '{image_path}' cargada en el formulario.")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo generar o mostrar la previsualización de la imagen. Error: {e}")

    def get_product_id_from_barcode(self):
        """
        Busca un producto en Odoo por su código de barras.

        Returns:
            int or None: El ID del producto si se encuentra, de lo contrario None.
        """
        barcodeProducto = str(self.main_window.txtCodigo.text())       
        if self.odoo_api:
            return self.odoo_api.find_product_by_barcode(barcodeProducto)
        print("ADVERTENCIA: No hay API de Odoo para get_product_id_from_barcode.")
        return None

    def handle_submit(self, codigonuevo):
        """
        Manejador para el botón 'Enviar'.
        Orquesta la creación del producto en Odoo y la actualización de
        propiedades en Inventor.

        Args:
            codigonuevo (str): El código del nuevo producto a crear.
        """
        usuario_logueado = self.odoo_connection_info.get('current_user_email', 'Desconocido')
        userlbl = user_service.get_user_full_name(usuario_logueado)

        new_product_id = self._create_product_in_odoo(codigonuevo)

        self.app.processEvents()

        if not new_product_id:
            self.main_window.lblMensaje_5.setText("Fallo al crear el producto en Odoo. No se puede continuar.")
            return

        self._update_inventor_properties(codigonuevo, userlbl)
        self.main_window.lblMensaje_5.setText("Producto cargado correctamente en Autodesk Inventor y ERP Odoo.")    
        GrSiFor = self.group_window.property("selected_group")
        if GrSiFor == "MATERIA PRIMA ENSAMBLE":
            self.main_window.btnEnviar.setEnabled(False)
            self.main_window.btnEnviar.setStyleSheet("background-color: gray; color: white")
            
            notification = Notification(
                title="Éxito",
                message="Producto creado y registrado correctamente.",
                parent=self.main_window
            )
            notification.show_centered()
            
            QTimer.singleShot(2000, self.quit_app)
        elif GrSiFor == "PRE-ENSAMBLES":
            self.main_window.btn650.setEnabled(True)
            self.main_window.btn650.setStyleSheet("")
            self.main_window.btnEnviar.setEnabled(False)
            self.main_window.btnEnviar.setStyleSheet("background-color: gray; color: white")
            self.main_window.btn650.setProperty("product_id", new_product_id)
        elif GrSiFor == "MATERIA PRIMA PROCESADA":
            self.main_window.btnMostrarMaterialBase.setEnabled(True)
            self.main_window.btnEnviar.setEnabled(False)
            self.main_window.btnEnviar.setStyleSheet("background-color: gray; color: white")
            self.main_window.btnMostrarMaterialBase.setProperty("product_id", new_product_id)
            self.main_window.setProperty("current_parent_product_id", new_product_id)
        else:
            self.main_window.lblMens1.setText("Selecciona un grupo para continuar.")

    def _update_labels_from_combobox(self):
        """
        Actualiza las etiquetas de categoría (Cat1, Cat2, Cat3) basadas en la
        selección actual del ComboBox de descripción.

        Returns:
            int or None: El ID de la categoría de nivel 3 seleccionada.
        """
        indice_seleccionado = self.main_window.ComboBoxDescripcion.currentIndex()
        if self.categorias_3 and len(self.categorias_3) > indice_seleccionado and indice_seleccionado >= 0:
            categoria_seleccionada = self.categorias_3[indice_seleccionado]
            cate2 = categoria_seleccionada['id']
            cate3 = categoria_seleccionada['x_descripcion']
            self.main_window.txtCat3.setText(str(cate3))
            cate_info = self._get_category_details(cate2)
            if cate_info:
                self.main_window.txtCat2.setText(str(cate_info['categoria_2'][1]))
                self.main_window.txtCat1.setText(str(cate_info['categoria_1'][1]))
            return cate2 

    def _get_category_details(self, cate2):
        """
        Obtiene los detalles de la jerarquía de categorías (1, 2, 3) desde Odoo.

        Args:
            cate2 (int): El ID de la categoría de nivel 3.

        Returns:
            dict or None: Un diccionario con la información de las categorías
                          padre si se encuentra, de lo contrario None.
        """
        if not self.odoo_api: return None
        variable = self.odoo_api.execute_kw('x_categoria_3', 'read', [[cate2]], {'fields': ['x_name', 'x_categoria_2']})
        if not variable: return None
        cate2_info = [variable[0]['id'], variable[0]['x_name']]
        id_categoria_2 = variable[0]['x_categoria_2']
        variable = self.odoo_api.execute_kw('x_categoria_2', 'read', [[id_categoria_2[0]]], {'fields': ['x_categoria_1']})
        if not variable: return None
        id_categoria_1 = variable[0]['x_categoria_1']
        return {'categoria_1': id_categoria_1, 'categoria_2': id_categoria_2, 'categoria_3': cate2_info}

    def load_session_config(self):
        """Carga la configuración de la última sesión desde config.json."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                last_user = config.get('last_user')
                last_pass = config.get('last_pass')

                if last_user and last_pass:
                    index = self.login_window.ComboBoxEmail.findText(last_user)
                    if index != -1:
                        self.login_window.ComboBoxEmail.setCurrentIndex(index)
                    self.login_window.txtClave.setText(last_pass)
                    print("INFO: Credenciales de sesión anterior cargadas.")
                    self.handle_login()
        except FileNotFoundError:
            print("INFO: No se encontró archivo de configuración. Se requiere inicio de sesión manual.")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo cargar la configuración de sesión: {e}")
            error_dialog = ErrorNotification(
                title="Error de Configuración",
                message="No se pudo leer el archivo de sesión (config.json).\n"
                        "Puede que esté corrupto. Se requerirá un inicio de sesión manual.",
                parent=self.login_window
            )
            error_dialog.show_centered()

    def handle_login(self):
        """Intenta autenticar al usuario en Odoo y avanza si tiene éxito."""
        usuario = self.login_window.ComboBoxEmail.currentText()
        clave = self.login_window.txtClave.text()

        if not usuario or not clave:
            self.login_window.lblMensaje.setText("Por favor, ingrese correo y contraseña.")
            return

        try:
            self.login_window.lblMensaje.setText("Autenticando...")
            self.odoo_api = OdooApi(self.URL_ODOO, self.DB_ODOO, usuario, clave)
            if self.odoo_api.connect():
                print("INFO: Autenticación exitosa.")
                self.odoo_connection_info = self.odoo_api.get_connection_info()
                try:
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump({'last_user': usuario, 'last_pass': clave}, f)
                except Exception as e:
                    print(f"ADVERTENCIA: No se pudo guardar el archivo de sesión: {e}")
                    error_dialog = ErrorNotification(
                        title="Error de Permisos",
                        message="No se pudo guardar la configuración de la sesión.\n\n"
                                "La aplicación funcionará, pero no podrá recordar sus credenciales la próxima vez.",
                        parent=self.group_window # Se muestra sobre la ventana que está a punto de aparecer
                    )
                    error_dialog.show_centered()
                
                self.post_login_setup()
                self.show_group_window()
            else:
                self.login_window.lblMensaje.setText("Error de autenticación. Verifique sus credenciales.")
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)

        except Exception as err:
            show_error_message("Error de Conexión", f"No se pudo conectar a Odoo en la URL:\n{self.URL_ODOO}\n\nVerifique la conexión de red o la configuración del servidor.", detailed_text=str(err))
            self.login_window.lblMensaje.setText("Error de conexión con Odoo.")

    def toggle_password_visibility(self):
        """Cambia la visibilidad del campo de la contraseña en el formulario de login."""
        if self.login_window.txtClave.echoMode() == QLineEdit.EchoMode.Password:
            self.login_window.txtClave.setEchoMode(QLineEdit.EchoMode.Normal)
            self.login_window.btnMostrarClave.setText("Ocultar")
        else:
            self.login_window.txtClave.setEchoMode(QLineEdit.EchoMode.Password)
            self.login_window.btnMostrarClave.setText("Ver")

    def handle_logout(self):
        """Cierra la sesión actual, borra el archivo de config y vuelve a la pantalla de login."""
        print("INFO: Cerrando sesión.")
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("INFO: Archivo de sesión eliminado.")
        self.group_window.close()
        self.login_window.show()

    def show_material_base_section(self):
        """
        Hace visible la sección de material base en la UI y carga los datos
        iniciales desde Inventor.
        """
        self.main_window.groupBox_MaterialBase.setVisible(True)
        sender_button = self.app.sender()
        product_id = sender_button.property("product_id")
        
        # Guardamos el ID del producto padre (el que se está creando/editando)
        # para que esté disponible al crear la línea de la BoM.
        if product_id:
             self.main_window.setProperty("current_parent_product_id", product_id)

        self.main_window.btnCargar_integrado.setProperty("product_id", product_id)
        self.get_material_base_from_inventor(product_id)

    def handle_existing_part_730(self):
        """
        Punto de entrada para el flujo de 'añadir material base a pieza existente'.
        """
        print("INFO: Botón 730 presionado. Iniciando flujo para pieza existente.")
        try:
            part_number = self.inventor_api.get_all_properties().get("part_number")
            if not part_number:
                QMessageBox.warning(self.main_window, "Pieza no registrada", "La pieza activa en Inventor no tiene un 'Part Number'.\n\nPor favor, utilice el flujo de creación de nuevo producto o asegúrese de que la pieza ya esté registrada.")
                return

            product_id = self.odoo_api.find_product_by_barcode(part_number)

            if not product_id:
                QMessageBox.critical(self.main_window, "Error de Búsqueda", f"La pieza con Part Number '{part_number}' no se encontró en Odoo.")
                return

            self.main_window.setProperty("current_parent_product_id", product_id)
            print(f"INFO: Pieza existente encontrada (ID: {product_id}). Mostrando sección de material base.")
            self.show_material_base_section()
        except Exception as e:
            show_error_message("Error en Flujo 730", f"Ocurrió un error al procesar la pieza existente: {e}")

    def _get_category_descriptions(self):
        """
        Obtiene todas las categorías de nivel 3 desde Odoo.

        Returns:
            list: Una lista de diccionarios, cada uno representando una categoría.
                  Retorna una lista vacía si falla la conexión.
        """
        if not self.odoo_api: return []
        return self.odoo_api.execute_kw('x_categoria_3', 'search_read', [], {'fields': ['id', 'x_name', 'x_descripcion']})

    def _populate_category_combobox(self):
        """
        Rellena el ComboBox de descripciones con las categorías obtenidas de Odoo.
        """
        self.main_window.ComboBoxDescripcion.clear()
        if self.categorias_3:
            self.categorias_3.sort(key=lambda cat: cat.get('x_name', ''))

            for categoria in self.categorias_3:
                descripcion = categoria.get('x_name', '')
                self.main_window.ComboBoxDescripcion.addItem(descripcion)

            completer = QCompleter(self.main_window.ComboBoxDescripcion.model(), self.main_window.ComboBoxDescripcion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.main_window.ComboBoxDescripcion.setCompleter(completer)

            self.main_window.ComboBoxDescripcion.currentIndexChanged.connect(self._update_labels_from_combobox)

    def open_bom_window(self):
        """
        Abre la ventana de Lista de Materiales (BoM) para un pre-ensamble.
        Pasa las instancias necesarias (inventor, app, odoo_api, etc.) a la nueva ventana.
        """
        from integrador.ui import bom_window
        product_id = self.main_window.btn650.property("product_id")
        bom_window.run_lista_materiales(self.inv, self.app, product_id, self.odoo_api, self.unit_service)
        self.main_window.close()

def run_app(inventor_instance):
    """Punto de entrada para el módulo de la UI."""
    q_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    # Aplicamos un estilo CSS a toda la aplicación para que los tooltips se vean más bonitos.
    q_app.setStyleSheet("""
        QToolTip {
            color: #71639e;
            background-color: #2a2a2a;
            border: 1px solid #71639e;
            border-radius: 4px;
            padding: 5px;
        }
    """)
    
    main_app = MainApplication(inventor_instance, q_app)
    main_app.run()
    
    sys.exit(q_app.exec())
