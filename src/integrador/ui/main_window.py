import random
import sys
import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QLineEdit, QMessageBox, QCompleter
from PyQt6.uic import loadUi

# Importamos la función de ayuda desde el módulo de utilidades
from integrador.utils.path_utils import show_error_message, resource_path
from integrador.api.inventor_api import InventorApi
from integrador.core.unit_service import UnitService
from integrador.ui.components.notification import Notification
from integrador.ui.components.error_notification import ErrorNotification
from integrador.core import user_service
from integrador.core.auth_service import AuthService
from integrador.core.product_flow_service import ProductFlowService
from integrador.core.processed_material_service import ProcessedMaterialService

# Rutas a los archivos de la interfaz de usuario
FORM_LOGIN_UI = resource_path("resources/ui/FormularioLogin.ui")
FORM_GRUPO_UI = resource_path("resources/ui/FormularioGrupo.ui")
FORM_ODOO_UI = resource_path("resources/ui/FormularioOdoo.ui")

APP_DATA_PATH = os.path.join(os.getenv('LOCALAPPDATA'), 'IntegradorOdooInventor') # Carpeta para datos de la app
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

        # Servicios
        self.auth_service = AuthService(url='http://192.168.10.13:8069', db='PruebaCFReA')
        self.odoo_api = None
        self.unit_service = None
        self.product_flow_service = None
        self.processed_material_service = None

        # Estado de la aplicación
        self.odoo_connection_info = {}
        self.categorias_3 = []

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
        self.main_window.btnValidar.clicked.connect(self.handle_validate_new_product)
        self.main_window.btnEnviar.clicked.connect(self.handle_submit_new_product)
        self.main_window.btnCerrarPrin.clicked.connect(self.quit_app)
        
        # Flujos secundarios
        self.main_window.btn650.clicked.connect(self.open_bom_window)
        self.main_window.btn730.clicked.connect(self.handle_existing_part_730)
        self.main_window.btnMostrarMaterialBase.clicked.connect(self.show_material_base_section)
        
        # Sección de material base integrado
        self.main_window.btnValidar_integrado.clicked.connect(self.handle_validate_base_material)
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
        self.odoo_api = self.auth_service.odoo_api
        self.unit_service = UnitService(self.odoo_api)
        self.product_flow_service = ProductFlowService(self.odoo_api, self.inventor_api, self.main_window, self.group_window)
        self.processed_material_service = ProcessedMaterialService(self.odoo_api, self.inventor_api, self.unit_service, self.main_window)
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

    def handle_validate_base_material(self):
        """
        Manejador para el botón 'Validar' en la sección de material base.
        Calcula y almacena la cantidad y unidad del material base.
        """
        if self.processed_material_service:
            self.processed_material_service.get_base_material_quantity(required_category=None)

    def handle_create_bom_for_product(self):
        """Crea o actualiza la BoM para un producto usando el material base del formulario."""
        if not self.processed_material_service: return
        
        if self.processed_material_service.create_bom_for_product():
            self.main_window.lblMensaje_3.setText("Lista de materiales actualizada con éxito.")
            self.main_window.btnCargar_integrado.setStyleSheet("background-color: blue; color: white;")
            self.main_window.btnCargar_integrado.setEnabled(False)
            
            Notification("Éxito", "El material base se ha asignado correctamente.", parent=self.main_window).show_centered()
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
                  
    def show_main_window(self):
        """
        Configura y muestra la ventana principal de la aplicación después de
        seleccionar un grupo.
        """
        if not self.product_flow_service: return
        
        codigo = self.product_flow_service.generate_unique_code()
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

    def handle_validate_new_product(self):
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

            # Asegurarse de que el directorio para la imagen exista antes de guardarla.
            # Esto previene un error si la carpeta 'resources/images' no ha sido creada.
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            self.inventor_api.capture_preview_image(image_path)
            pixmap = QPixmap(image_path)
            self.main_window.lblImagen.setPixmap(pixmap)
            print(f"INFO: Previsualización de imagen '{image_path}' cargada en el formulario.")
        except Exception as e:
            print(f"ADVERTENCIA: No se pudo generar o mostrar la previsualización de la imagen. Error: {e}")

    def handle_submit_new_product(self):
        """
        Manejador para el botón 'Enviar'.
        Orquesta la creación del producto en Odoo y la actualización de
        propiedades en Inventor.
        """
        if not self.product_flow_service: return

        usuario_logueado = self.odoo_connection_info.get('current_user_email', 'Desconocido')
        userlbl = user_service.get_user_full_name(usuario_logueado)

        new_product_id = self.product_flow_service.create_product_in_odoo()
        self.app.processEvents()

        if not new_product_id:
            self.main_window.lblMensaje_5.setText("Fallo al crear el producto en Odoo. No se puede continuar.")
            return

        self.product_flow_service.update_inventor_properties(new_product_id, userlbl, usuario_logueado)
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
            self.main_window.setProperty("selected_category_id", cate2)
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
        config = self.auth_service.load_session()
        if config:
            last_user = config.get('last_user')
            last_pass = config.get('last_pass')
            if last_user and last_pass:
                index = self.login_window.ComboBoxEmail.findText(last_user)
                if index != -1:
                    self.login_window.ComboBoxEmail.setCurrentIndex(index)
                self.login_window.txtClave.setText(last_pass)
                self.handle_login() # Intenta autologin
        else:
            print("INFO: No se encontró archivo de configuración. Se requiere inicio de sesión manual.")

    def handle_login(self):
        """Intenta autenticar al usuario en Odoo y avanza si tiene éxito."""
        usuario = self.login_window.ComboBoxEmail.currentText()
        clave = self.login_window.txtClave.text()

        if not usuario or not clave:
            self.login_window.lblMensaje.setText("Por favor, ingrese correo y contraseña.")
            return

        try:
            self.login_window.lblMensaje.setText("Autenticando...")
            self.app.processEvents()

            odoo_api_instance = self.auth_service.login(usuario, clave)
            if odoo_api_instance:
                print("INFO: Autenticación exitosa.")
                self.odoo_connection_info = odoo_api_instance.get_connection_info()
                self.post_login_setup()
                self.show_group_window()
            else:
                self.login_window.lblMensaje.setText("Error de autenticación. Verifique sus credenciales.")

        except Exception as err:
            show_error_message("Error de Conexión", f"No se pudo conectar a Odoo.\n\nVerifique la conexión de red o la configuración del servidor.", detailed_text=str(err))
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
        self.auth_service.logout()
        self.group_window.close()
        self.login_window.show()

    def show_material_base_section(self):
        """
        Hace visible la sección de material base en la UI y carga los datos
        iniciales desde Inventor.
        """
        self.main_window.groupBox_MaterialBase.setVisible(True)
        sender_button = self.app.sender()
        parent_product_id = sender_button.property("product_id")
        
        if parent_product_id:
             self.main_window.setProperty("current_parent_product_id", parent_product_id)

        if self.processed_material_service:
            self.processed_material_service.get_base_material_from_inventor()

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

            product_id = self.auth_service.odoo_api.find_product_by_barcode(part_number)

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
        if not self.auth_service.odoo_api: return []
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
        bom_window.run_lista_materiales(self.inv, self.app, product_id, self.auth_service.odoo_api, self.unit_service)
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
