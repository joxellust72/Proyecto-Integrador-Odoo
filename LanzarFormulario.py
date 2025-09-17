import random
import win32com.client as win32  # Libreria API Autodesk
import xmlrpc.client  # Libreria API Odoo
import sys
import os # <--- IMPORTANTE: Añadimos el módulo 'os'
import json # <-- Añadimos el módulo JSON para manejar la configuración
import base64 # <-- Añadimos el módulo base64
from PyQt6.QtGui import QPixmap # <-- Importamos QPixmap para manejar imágenes
from PyQt6.QtCore import Qt # <-- Importamos Qt para el manejo de filtros
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget, QPushButton, QLineEdit, QMessageBox, QCompleter
from PyQt6.uic import loadUi

# --- CONSTRUCCIÓN DE RUTAS ABSOLUTAS ---
# Esto asegura que el script siempre encuentre sus archivos .ui, sin importar desde dónde se ejecute.
# Obtenemos la ruta del directorio donde se encuentra este script.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Construimos la ruta completa para cada archivo .ui
FORM_LOGIN_UI = os.path.join(BASE_DIR, "FormularioLogin.ui") # <-- NUEVO
FORM_GRUPO_UI = os.path.join(BASE_DIR, "FormularioGrupo.ui")
FORM_ODOO_UI = os.path.join(BASE_DIR, "FormularioOdoo.ui")
FORM_MATERIAL_BASE_UI = os.path.join(BASE_DIR, "FormularioMaterialBase.ui")
FORM_LISTA_MATERIALES_UI = os.path.join(BASE_DIR, "FormularioListaMateriales.ui")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json") # <-- Ruta para nuestro archivo de sesión
# --- FIN DE LA CONSTRUCCIÓN DE RUTAS ---
from ui_utils import show_error_message


def validar_docActivo_inventor():   
    try:
        # En modo simulación, esto no se ejecutará, pero lo dejamos para el modo real.
        invApp = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition
        def encode_image_to_base64(image_path):
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image

        def imagen():
            Objeto_Aplicacion_Inevntor = inv.ActiveDocument.ComponentDefinitions.Item(1).Application
            Camara = Objeto_Aplicacion_Inevntor.ActiveView.Camera
            Camara.ViewOrientationType = 10761
            Camara.ApplyWithoutTransition()
            Camara.ViewOrientationType = 10760
            Camara.ApplyWithoutTransition()
            image_path = 'O:/5.OPERACIONES/AT/Odoo/LibImaOddo/Imagen.png'
            Objeto_Aplicacion_Inevntor = Objeto_Aplicacion_Inevntor.ActiveDocument
            Objeto_Aplicacion_Inevntor.SaveAs(image_path,True)
            return encode_image_to_base64(image_path) 
        # imagen() # Comentado para evitar errores de ruta en modo simulación      
        return True
    except Exception as e:
        # Este bloque se ejecutará en modo simulación
        print(f"INFO (validar_docActivo_inventor): Se capturó la excepción esperada: {e}")
        # No hacemos nada aquí porque la carga de formularios se hace en run_app
        return True # Devolvemos True para que la ejecución continúe
    
def on_clickCerrar():
    if app:
        app.quit()

#region Funciones Movidas de LanzarMaterialBase1
def get_material_base_from_inventor_integrado(product_id):
    """
    Lee la iProperty 'Codigo Sizfra' de Inventor, busca el producto en Odoo
    y actualiza el formulario integrado.
    """
    try:
        codigo_sizfra = ""
        custom_props = inv.ActiveDocument.PropertySets.Item("User Defined Properties")
        try:
            codigo_sizfra = custom_props.Item("CODIGO SIZFRA").Value
        except (AttributeError, KeyError, Exception):
            print("ADVERTENCIA: La iProperty 'Codigo Sizfra' no existe en el documento. Se asumirá como vacía.")

        if not codigo_sizfra:
            QMessageBox.critical(form_odoo, "Error", "La iProperty 'Codigo Sizfra' no puede estar vacía en el documento de Inventor.")
            return False

        codigo_sizfra = str(int(float(codigo_sizfra))).strip()

        search_domain = ['|', ['default_code', '=', codigo_sizfra], ['barcode', '=', codigo_sizfra]]
        product_ids = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'product.product', 'search_read', [search_domain], {'fields': ['id', 'name', 'default_code'], 'limit': 1})

        if not product_ids:
            error_msg = f"No se encontró material base en Odoo con el código '{codigo_sizfra}' (ni como Ref. Interna ni como Cód. Barras)."
            QMessageBox.critical(form_odoo, "Error de Búsqueda", error_msg)
            return False

        product_name = product_ids[0]['name']
        found_code = product_ids[0].get('default_code') or codigo_sizfra
        form_odoo.txtMaterialBase_integrado.setText(found_code)
        form_odoo.lblMensaje_3.setText(f"Material base '{product_name}' (código: {found_code}) cargado.")
        return True

    except Exception as e:
        error_msg = f"No se pudo leer la propiedad 'Codigo Sizfra' de Inventor. Asegúrese de que exista. Error: {e}"
        print(f"ERROR: {error_msg}")
        QMessageBox.critical(form_odoo, "Error de Inventor", error_msg)
        return False

def obtener_id_material_base_integrado():
    CodigoMaterialBase = str(form_odoo.txtMaterialBase_integrado.text()).strip()
    if not odoo_connection['models']: return None
    search_domain = ['|', ['default_code', '=', CodigoMaterialBase], ['barcode', '=', CodigoMaterialBase]]
    search_result = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'product.product', 'search', [search_domain], {'limit': 1})
    return search_result[0] if search_result else None

def obtener_unidad_material_base_integrado():
    if not odoo_connection['models']: return ""
    material_base_ids_prod = obtener_id_material_base_integrado()
    if not material_base_ids_prod:
        return ""
    product_datauom = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'product.product', 'read', [material_base_ids_prod], {'fields': ['uom_id']})
    uom_id = product_datauom[0]['uom_id']
    uom_data = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'uom.uom', 'read', [uom_id[0]], {'fields': ['name']})
    return uom_data[0]['name']

def obtener_cantidad_material_base_integrado():
    if not inv: return 0
    props = inv.ActiveDocument.PropertySets
    uom_data1 = obtener_unidad_material_base_integrado()
    if uom_data1 == "kg":
        mass = str(round(props.Item("Design Tracking Properties").Item("Mass").Value / 1000, 2))
        mass_in_kg_str = mass + " kg"
        ValueOdoo = float(mass)
        form_odoo.txtCantReq_integrado.setText(str(mass_in_kg_str))
        form_odoo.txtCantReq_integrado.setReadOnly(True)
        return ValueOdoo
    else:
        ValueOdooForm = inv.ActiveDocument.ComponentDefinition.BOMQuantity.UnitQuantity
        if ValueOdooForm == "" or "Mock" in inv.__class__.__name__:
            ValueOdoo = 1
            form_odoo.txtCantReq_integrado.setText(str("1 Uni"))
            form_odoo.txtCantReq_integrado.setReadOnly(True)
        else:
            ValueOdoo = float(ValueOdooForm.split(" ")[0])
            form_odoo.txtCantReq_integrado.setText(str(ValueOdooForm))
            form_odoo.txtCantReq_integrado.setReadOnly(True)
        return ValueOdoo if ValueOdoo else 1

def on_click_validar_integrado():
    obtener_cantidad_material_base_integrado()

def create_bom_for_product_integrado(product_id):
    material_base_ids_prod = obtener_id_material_base_integrado()
    if not material_base_ids_prod:
        QMessageBox.critical(form_odoo, "Error", "No se pudo encontrar el material base en Odoo. Verifique el código.")
        return

    bom_ids = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'mrp.bom', 'search', [[['product_tmpl_id', '=', product_id]]], {'limit': 1})
    if bom_ids:
        listacreada = bom_ids[0]
    else:
        vals = [{'product_tmpl_id': product_id, 'product_qty': 1}]
        new_bom_id = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'mrp.bom', 'create', [vals])
        listacreada = new_bom_id[0] if new_bom_id else None

    if not listacreada:
        QMessageBox.critical(form_odoo, "Error", "No se pudo crear o encontrar la lista de materiales para el producto padre.")
        return

    uom_name = obtener_unidad_material_base_integrado()
    uom_id_result = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'uom.uom', 'search', [[('name', '=', uom_name)]])
    uom_id = uom_id_result[0] if uom_id_result else 1

    ValueOdoo = obtener_cantidad_material_base_integrado()
    vals = [{'bom_id': listacreada, 'product_id': material_base_ids_prod, 'product_qty': ValueOdoo, 'product_uom_id': uom_id}]
    listacargada = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'], 'mrp.bom.line', 'create', [vals])

    form_odoo.lblMensaje_3.setText(f"Lista de materiales actualizada con éxito. Línea ID: {listacargada}")
    form_odoo.btnCargar_integrado.setStyleSheet("background-color: blue; color: white;")
    form_odoo.btnCargar_integrado.setEnabled(False)

#endregion

def valida_cate_grupo():
    GrSiFor = form_grupo.property("selected_group") # Usamos la propiedad que guardamos
    if GrSiFor == "MATERIA PRIMA ENSAMBLE":       
        form_odoo.txtCategoria.setText("MATERIA PRIMA ENSAMBLE")
    elif GrSiFor == "PRE-ENSAMBLES":        
        form_odoo.txtCategoria.setText("PRE-ENSAMBLES")         
    elif GrSiFor == "MATERIA PRIMA PROCESADA":
        form_odoo.txtCategoria.setText("MATERIA PRIMA PROCESADA")
                  
def generar_codigo_unico(form_grupo):
    GrSiFor = form_grupo.property("selected_group") # Usamos la propiedad que guardamos
    if GrSiFor == "MATERIA PRIMA ENSAMBLE":
        grupoNum = "600"
        form_grupo.lblMensaje.setText("Codigo generado con exito.")
    elif GrSiFor == "PRE-ENSAMBLES":
        grupoNum = "650"
        form_grupo.lblMensaje.setText("Codigo generado con exito.")    
    elif GrSiFor == "MATERIA PRIMA PROCESADA":
        grupoNum = "730"
        form_grupo.lblMensaje.setText("Codigo generado con exito.")
    else:
        form_grupo.lblMensaje.setText("Selecciona el grupo")
        return None
        
    rand = random.randrange(1, 9999999999)
    numero_aleatorio_formateado = "{:010d}".format(rand)
    codigonuevo = grupoNum + numero_aleatorio_formateado
    return codigonuevo

def API_Odoo(codigonuevo):
    codigonuevo = form_odoo.txtCodigo.text()    
    Material = str(form_odoo.txtMaterial.text())
    Masa = str(form_odoo.txtMasa.text())
    volume = str(form_odoo.txtVolume.text())
    GrSiFor = form_grupo.property("selected_group") # Usamos la propiedad que guardamos
    nombre = form_odoo.txtNombreSis.text()
    clases = actualizar_labels_desde_combobox()
    acabado = form_odoo.txtAcabado.text()
    descripcion = form_odoo.txtDescripcion.text()
    subject = form_odoo.txtAlmacena.text()    
    # email = form_odoo.ComboBoxEmail.currentText() # Eliminado, ya no existe en el form
    palabclave = form_odoo.textPalabraClave.toPlainText()
    path = inv.ActiveDocument.FullFileName # Usamos la instancia global 'inv'

    def encode_image_to_base64(image_path):
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image

    def imagen():
        # Esta función fallará en modo simulación si no existe la ruta.
        # La dejamos para el modo real, pero podría necesitar un try/except.
        try:
            Objeto_Aplicacion_Inevntor = inv.ActiveDocument.ComponentDefinitions.Item(1).Application
            Camara = Objeto_Aplicacion_Inevntor.ActiveView.Camera
            Camara.ViewOrientationType = 10761
            Camara.ApplyWithoutTransition()
            Camara.ViewOrientationType = 10760
            Camara.ApplyWithoutTransition()
            image_path = 'O:/5.OPERACIONES/AT/Odoo/LibImaOddo/Imagen.png'
            Objeto_Aplicacion_Inevntor = Objeto_Aplicacion_Inevntor.ActiveDocument
            Objeto_Aplicacion_Inevntor.SaveAs(image_path,True)
            return encode_image_to_base64(image_path)
        except Exception as img_err:
            print(f"ADVERTENCIA: No se pudo generar la imagen. {img_err}")
            return "" # Devolvemos una cadena vacía si falla
    
    imagen_b64 = imagen()
    
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
        'image_1920': imagen(), # Llamamos a la función aquí para generar y mostrar la imagen
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

    try:
        new_product_id = odoo_connection['models'].execute_kw(odoo_connection['db'], odoo_connection['uid'], odoo_connection['pass'],'product.template', 'create', [new_product_data])
        print("Nuevo producto creado en el ERP Odoo con ID:", new_product_id)
        form_odoo.lblMens1.setText(f"Nuevo producto creado en el ERP Odoo con ID: {new_product_id}")
        return new_product_id # <-- DEVOLVEMOS EL ID DEL PRODUCTO CREADO
                    
    except xmlrpc.client.Fault as error:
        if 'Códigos de barras ya asignados' in error.faultString:
            start_index = error.faultString.find('"') + 1
            end_index = error.faultString.find('"', start_index)
            codigo_repetido = error.faultString[start_index:end_index]
            print("Código de producto repetido:", codigo_repetido)
            form_odoo.lblMens1.setText(f"Código de producto repetido: {codigo_repetido}")
            form_odoo.lblMensaje.setText("El código de barras está repetido. Saliendo del programa.")
            return None # Devolvemos None si falla
        raise # Si es otro tipo de Fault, lo relanzamos para que lo capture el hook global
    

def API_Autodesk_Inventor_imput(codigonuevo, designer):    
    codigonuevo = form_odoo.txtCodigo.text()
    cate = form_odoo.txtCategoria.text()
    cat1 = form_odoo.txtCat1.text()
    cat2 = form_odoo.txtCat2.text()
    cat3 = form_odoo.txtCat3.text()
    autor = odoo_connection.get('current_user_email', '') # Obtenemos el email del usuario logueado
    palabclave = form_odoo.textPalabraClave.toPlainText()
    product_ids = obtener_id_product()
    new_product_id = product_ids   
    
    part = invDoc.ComponentDefinition
    part_number_property = part.Document.PropertySets.Item("Design Tracking Properties").Item("Part Number")
    new_part_number = codigonuevo
    part_number_property.Value = new_part_number
    print("Se ha establecido el nuevo número de pieza en Autodesk Inventor:", new_part_number)
    form_odoo.lblMensaje.setText(f"Se ha establecido el nuevo número de pieza en Autodesk Inventor: {new_part_number}")
    
    categoria_property = part.Document.PropertySets.Item("Inventor Document Summary Information").Item("Category")
    new_categoria = cate.lower()
    categoria_property.Value = new_categoria
    print("Se ha establecido la nueva categoria de la pieza en Autodesk Inventor:", new_categoria)  
    form_odoo.lblMensaje_4.setText(f"Se ha establecido la nueva categoria de la pieza en Autodesk Inventor: {new_categoria}")
    
    categoria_designer = part.Document.PropertySets.Item("Design Tracking Properties").Item("Designer")
    new_designer = designer
    categoria_designer.Value = new_designer 
    print("Se ha establecido el diseñador de la pieza en Autodesk Inventor:", new_designer)  
    
    categoria_stock_number = part.Document.PropertySets.Item("Design Tracking Properties").Item("Stock Number")
    new_stock_number = new_product_id 
    categoria_stock_number.Value = new_stock_number 
    print("Se ha establecido el diseñador de la pieza en Autodesk Inventor:", new_stock_number)    
    
    categoria_autor = part.Document.PropertySets.Item("Inventor Summary Information").Item("Author")
    new_autor = autor
    categoria_autor.Value = new_autor 
    print("Se ha establecido el autor de la pieza en Autodesk Inventor:", new_autor)  
    
    categoria_PalabraClave = part.Document.PropertySets.Item("Inventor Summary Information").Item("Keywords")
    new_PalabraClave = palabclave
    categoria_PalabraClave.Value = new_PalabraClave 
    print("Se ha establecido las palabras claves de la pieza en Autodesk Inventor:", new_PalabraClave)
    form_odoo.lblMensaje_5.setText(f"Se ha establecido las palabras claves de la pieza en Autodesk Inventor: {new_PalabraClave}")   
    
    custom_properties = {
        "Clase 1": cat1,
        "Clase 2": cat2,
        "Clase 3": cat3            
    }
    for property_name, value in custom_properties.items():
        try:
            custom_property = part.Document.PropertySets.Item("User Defined Properties").Item(property_name)
            custom_property.Value = value
            print(f"Se ha establecido la propiedad en Autodesk Inventor '{property_name}' con el valor: {value}")
        except Exception:
            # Este error es menos crítico, podemos advertir y continuar
            print(f"ADVERTENCIA: No se pudo establecer la propiedad personalizada '{property_name}' en Inventor.")

    invDoc.Save()

def validar_barcode():
    props = inv.ActiveDocument.ComponentDefinition.Document.PropertySets
    valbarcode = props.Item("Design Tracking Properties").Item("Part Number").Value
    mate = props.Item("Design Tracking Properties").Item("Material").Value
    descripcion = props.Item("Design Tracking Properties").Item("Description").Value
    almacena = props.Item("Inventor Summary Information").Item("Subject").Value
    acab = props.Item("Design Tracking Properties").Item("Appearance").Value
    masa = props.Item("Design Tracking Properties").Item("Mass").Value
    cat1 = props.Item("User Defined Properties").Item("Clase 1").Value
    cat2 = props.Item("User Defined Properties").Item("Clase 2").Value
    cat3 = props.Item("User Defined Properties").Item("Clase 3").Value
    nomsis = props.Item("Inventor Summary Information").Item("Title").Value
    volume = props.Item("Design Tracking Properties").Item("Volume").Value
    cate = props.Item("Inventor Document Summary Information").Item("Category").Value
    palabclave = props.Item("Inventor Summary Information").Item("Keywords").Value
  
    if valbarcode == "":                
        form_odoo.lblMensaje.setText("Autodesk Inventor esta listo para recibir su carga.")
        return False
    else:                         
        form_odoo.txtCodigo.setText(valbarcode)
        form_odoo.txtCodigo.setReadOnly(True)
        form_odoo.txtNombreSis.setText(nomsis)
        form_odoo.txtNombreSis.setReadOnly(True)
        form_odoo.txtCat1.setText(cat1)
        form_odoo.txtCat1.setReadOnly(True)
        form_odoo.txtCat2.setText(cat2)
        form_odoo.txtCat2.setReadOnly(True)
        form_odoo.txtCat3.setText(cat3)
        form_odoo.txtCat3.setReadOnly(True)
        form_odoo.txtMaterial.setText(mate)
        form_odoo.txtMaterial.setReadOnly(True)
        form_odoo.txtAcabado.setText(acab)
        form_odoo.txtAcabado.setReadOnly(True)
        form_odoo.txtMasa.setText(str(round(masa/1000,2)))
        form_odoo.txtMasa.setReadOnly(True)
        form_odoo.lblMensaje.setText("Datos obtenidos de Autodesk Inventor.")
        form_grupo.close()
        form_odoo.btnEnviar.setEnabled(False)
        form_odoo.btnEnviar.setStyleSheet("background-color: gray; color: white")
        form_odoo.txtDescripcion.setText(descripcion)
        form_odoo.txtDescripcion.setReadOnly(True)
        form_odoo.txtAlmacena.setText(almacena)
        form_odoo.txtAlmacena.setReadOnly(True)
        form_odoo.txtCategoria.setText(cate)
        form_odoo.txtCategoria.setReadOnly(True)
        form_odoo.txtVolume.setText(str(round(volume/1,2)))
        form_odoo.txtVolume.setReadOnly(True)
        form_odoo.textPalabraClave.setText(palabclave)
        form_odoo.textPalabraClave.setReadOnly(True)
        return True

def abrir_formulario_principal():
    codigo = generar_codigo_unico(form_grupo)
    valida_cate_grupo()      
    form_odoo.txtCodigo.setText(codigo) 
    form_odoo.txtCodigo.setReadOnly(True)
    form_odoo.lblMens1.setText("Aplicativo listo para conectar con Autodesk Inventor, ERP Odoo, Sistema información Sizfra, ")
    form_odoo.show()
    form_grupo.close()
    return(codigo)

def on_grupo_button_clicked():
    """Maneja el clic de cualquiera de los tres botones de grupo."""
    # Identifica qué botón fue presionado
    sender = app.sender()
    group_name = sender.text().split(' (')[0] # Extrae el nombre del grupo del texto del botón
    
    # Guardamos el grupo seleccionado en una propiedad dinámica del formulario para usarlo después
    form_grupo.setProperty("selected_group", group_name)
    
    # Llamamos a la función que abre el siguiente formulario
    abrir_formulario_principal()

def abrir_formulario_grupo():
    form_login.close()
    global invDoc

    # --- CORRECCIÓN MODO REAL vs SIMULACIÓN ---
    # Solo creamos un nuevo documento si estamos en modo simulación.
    # En modo real, asumimos que el usuario ya tiene el documento correcto abierto.
    if "MockApplication" in inv.__class__.__name__:
        invDoc = inv.CreateNewDocument()
        print(f"INFO: Nuevo documento simulado '{invDoc.Name}' está activo.")
    
    form_grupo.show()

def on_click_validar():
    print("INFO: Botón 'Validar' presionado. Rellenando campos desde el simulador.")     
    props = inv.ActiveDocument.ComponentDefinition.Document.PropertySets
    mate = props.Item("Design Tracking Properties").Item("Material").Value
    descripcion = props.Item("Design Tracking Properties").Item("Description").Value
    almacena = props.Item("Inventor Summary Information").Item("Subject").Value
    acab = props.Item("Design Tracking Properties").Item("Appearance").Value
    masa = props.Item("Design Tracking Properties").Item("Mass").Value
    volume = props.Item("Design Tracking Properties").Item("Volume").Value
    nombre = props.Item("Inventor Summary Information").Item("Title").Value
    palabclave = props.Item("Inventor Summary Information").Item("Keywords").Value
    codigo_inventor = props.Item("Design Tracking Properties").Item("Part Number").Value
    categoria_inventor = props.Item("Inventor Document Summary Information").Item("Category").Value
    
    # Obtenemos el email del usuario que inició sesión
    usuario_logueado = odoo_connection.get('current_user_email', 'Desconocido')
    
    if usuario_logueado == "admin@automate-corp.com": userlbl = "Administrador"  
    elif usuario_logueado == "it@automate-corp.com": userlbl = "Christiam Fernando Rey Anaya"          
    elif usuario_logueado == "ingenieria1@automate-corp.com": userlbl = "Jesus Alberto Ariza Gil"    
    elif usuario_logueado == "ingenieria2@automate-corp.com": userlbl = "Sara Zambrano Naranjo"
    elif usuario_logueado == "ingenieria3@automate-corp.com": userlbl = "Carlos Alberto Chavarria Jaramillo"
    elif usuario_logueado == "ingenieria4@automate-corp.com": userlbl = "Juan Carlos Atehortúa Montes" 
    elif usuario_logueado == "ingenieria5@automate-corp.com": userlbl = "Andres Felipe Marin Quintero" 
    elif usuario_logueado == "ingenieria6@automate-corp.com": userlbl = "Daniel Londoño Serna" 
    elif usuario_logueado == "electrica@automate-corp.com": userlbl = "Monica Yepes Medina" 
    elif usuario_logueado == "produccion@automate-corp.com": userlbl = "Johan Sebastian Gaviria Ruiz"  
    elif usuario_logueado == "sistemas@automate-corp.com": userlbl = "Juan Andres Pernet"   
    elif usuario_logueado == "operaciones@automate-corp.com": userlbl = "Juan Alejandro Diaz"                
    else:
        userlbl = usuario_logueado
                     
    if nombre == "":        
        form_odoo.lblMensaje_5.setText("No se encontraron datos en el documento simulado.")
        return False
    else:
        # Rellenamos los campos que faltaban
        # --- CORRECCIÓN CLAVE ---
        # No sobrescribimos el código si ya fue generado.
        if not form_odoo.txtCodigo.text():
            form_odoo.txtCodigo.setText(codigo_inventor)
        form_odoo.txtDescripcion.setText(descripcion)
        form_odoo.txtDescripcion.setReadOnly(True)
        form_odoo.txtAlmacena.setText(almacena)
        form_odoo.txtAlmacena.setReadOnly(True)
        form_odoo.txtNombreSis.setText(nombre)
        form_odoo.txtNombreSis.setReadOnly(True)
        form_odoo.txtMaterial.setText(mate)
        form_odoo.txtMaterial.setReadOnly(True)
        form_odoo.txtAcabado.setText(acab)
        form_odoo.txtAcabado.setReadOnly(True)
        form_odoo.txtMasa.setText(str(round(masa/1000,2)))
        form_odoo.txtMasa.setReadOnly(True)
        form_odoo.lblMensaje.setText("Datos obtenidos del aplicativo Autodesk Inventor Professional.")
        # form_odoo.lblMensaje_6.setText(userlbl) # <-- Eliminamos esta línea porque el widget ya no existe
        form_odoo.txtCategoria.setText(categoria_inventor)
        form_odoo.txtCategoria.setReadOnly(True)
        form_odoo.lblMens1.setText("Bienvenido,"+ userlbl)
        form_odoo.btnValidar.setStyleSheet("background-color: blue; color: white;")
        form_odoo.txtVolume.setText(str(round(volume/1,2)))
        form_odoo.txtVolume.setReadOnly(True)
        form_odoo.textPalabraClave.setText(palabclave)
        form_odoo.textPalabraClave.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.lblMensaje_5.setText("Codigo creado con exito")#, generar_codigo_unico(form_grupo))
                 
def obtener_id_product():
    barcodeProducto = str(form_odoo.txtCodigo.text())       
    if odoo_connection and odoo_connection.get('models'):
        conn = odoo_connection
        product_ids = conn['models'].execute_kw(conn['db'], conn['uid'], conn['pass'], 'product.template', 'search', [[['barcode', '=', barcodeProducto]]])
        return product_ids[0] if product_ids else None
    print("ADVERTENCIA: No hay conexión a Odoo para obtener_id_product.")
    return None

def on_click(codigonuevo):
    descripcionfor = form_odoo.ComboBoxDescripcion.currentText()
    # --- INICIO DE LA CORRECCIÓN ---
    # Obtenemos el nombre del diseñador (userlbl) aquí, antes de llamar a las APIs.
    usuario_logueado = odoo_connection.get('current_user_email', 'Desconocido')
    if usuario_logueado == "admin@automate-corp.com": userlbl = "Administrador"
    elif usuario_logueado == "it@automate-corp.com": userlbl = "Christiam Fernando Rey Anaya"
    elif usuario_logueado == "ingenieria1@automate-corp.com": userlbl = "Jesus Alberto Ariza Gil"
    elif usuario_logueado == "ingenieria2@automate-corp.com": userlbl = "Sara Zambrano Naranjo"
    elif usuario_logueado == "ingenieria3@automate-corp.com": userlbl = "Carlos Alberto Chavarria Jaramillo"
    elif usuario_logueado == "ingenieria4@automate-corp.com": userlbl = "Juan Carlos Atehortúa Montes"
    elif usuario_logueado == "ingenieria5@automate-corp.com": userlbl = "Andres Felipe Marin Quintero"
    elif usuario_logueado == "ingenieria6@automate-corp.com": userlbl = "Daniel Londoño Serna"
    elif usuario_logueado == "electrica@automate-corp.com": userlbl = "Monica Yepes Medina"
    elif usuario_logueado == "produccion@automate-corp.com": userlbl = "Johan Sebastian Gaviria Ruiz"
    elif usuario_logueado == "sistemas@automate-corp.com": userlbl = "Juan Andres Pernet"
    elif usuario_logueado == "operaciones@automate-corp.com": userlbl = "Juan Alejandro Diaz"
    else:
        userlbl = usuario_logueado
    # --- FIN DE LA CORRECCIÓN ---
    new_product_id = API_Odoo(codigonuevo) # Capturamos el ID del nuevo producto

    if not new_product_id:
        form_odoo.lblMensaje_5.setText("Fallo al crear el producto en Odoo. No se puede continuar.")
        return # Si no se creó el producto, no continuamos

    API_Autodesk_Inventor_imput(codigonuevo, userlbl) # Pasamos el nombre del diseñador
    form_odoo.lblMensaje_5.setText("Producto cargado correctamente en Autodesk Inventor y ERP Odoo.")    
    GrSiFor = form_grupo.property("selected_group") # Usamos la propiedad que guardamos
    if GrSiFor == "MATERIA PRIMA ENSAMBLE":
        form_odoo.lblMens1.setText("Producto creado con éxito.")
        # Podríamos cerrar la app o mostrar un mensaje de éxito final.
        # Por ahora, deshabilitamos el botón para evitar reenvíos.
        form_odoo.btnEnviar.setEnabled(False)
        form_odoo.btnEnviar.setStyleSheet("background-color: gray; color: white")
    elif GrSiFor == "PRE-ENSAMBLES": # Para Pre-Ensambles, habilitamos el botón 650
        form_odoo.btn650.setEnabled(True)
        form_odoo.btn650.setStyleSheet("") # Restaura el estilo por defecto
        form_odoo.btnEnviar.setEnabled(False)
        form_odoo.btnEnviar.setStyleSheet("background-color: gray; color: white")
        # Guardamos el ID del producto en el botón para usarlo después
        form_odoo.btn650.setProperty("product_id", new_product_id)
    elif GrSiFor == "MATERIA PRIMA PROCESADA":
        form_odoo.btnMostrarMaterialBase.setEnabled(True)
        form_odoo.btnEnviar.setEnabled(False)
        form_odoo.btnEnviar.setStyleSheet("background-color: gray; color: white")
        form_odoo.btnMostrarMaterialBase.setProperty("product_id", new_product_id)
    else:
        form_odoo.lblMens1.setText("Selecciona un grupo para continuar.")


def actualizar_labels_desde_combobox():
    indice_seleccionado = form_odoo.ComboBoxDescripcion.currentIndex()
    if categorias_3 is not None and len(categorias_3) > indice_seleccionado and indice_seleccionado >= 0:
        categoria_seleccionada = categorias_3[indice_seleccionado]
        cate2 = categoria_seleccionada['id']
        cate3 = categoria_seleccionada['x_descripcion']
        form_odoo.txtCat3.setText(str(cate3))
        cate_info = metodo_categorias(cate2, odoo_connection) # <-- Pasar la conexión
        if cate_info:
            form_odoo.txtCat2.setText(str(cate_info['categoria_2'][1]))
            form_odoo.txtCat1.setText(str(cate_info['categoria_1'][1]))
        return cate2 

def metodo_categorias(cate2, connection):
    if not connection or not connection.get('models'): return None    
    variable = connection['models'].execute_kw(connection['db'], connection['uid'], connection['pass'], 'x_categoria_3', 'read', [[cate2]], {'fields': ['x_name', 'x_categoria_2']})
    cate2_info = [variable[0]['id'], variable[0]['x_name']]
    id_categoria_2 = variable[0]['x_categoria_2']
    variable = connection['models'].execute_kw(connection['db'], connection['uid'], connection['pass'], 'x_categoria_2', 'read', [[id_categoria_2[0]]], {'fields': ['x_categoria_1']})
    id_categoria_1 = variable[0]['x_categoria_1']
    return {'categoria_1': id_categoria_1, 'categoria_2': id_categoria_2, 'categoria_3': cate2_info}

def load_session_config():
    """Carga la configuración de la última sesión desde config.json."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                last_user = config.get('last_user')
                last_pass = config.get('last_pass')

                if last_user and last_pass:
                    index = form_login.ComboBoxEmail.findText(last_user)
                    if index != -1:
                        form_login.ComboBoxEmail.setCurrentIndex(index)
                    form_login.txtClave.setText(last_pass)
                    print("INFO: Credenciales de sesión anterior cargadas.")
                    # Intentar login automático
                    on_click_iniciar_sesion()
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo cargar la configuración de sesión: {e}")

def on_click_iniciar_sesion():
    """Intenta autenticar al usuario en Odoo y avanza si tiene éxito."""
    usuario = form_login.ComboBoxEmail.currentText()
    clave = form_login.txtClave.text()

    if not usuario or not clave:
        form_login.lblMensaje.setText("Por favor, ingrese correo y contraseña.")
        return

    try:
        form_login.lblMensaje.setText("Autenticando...")
        # Usamos la conexión global de admin para verificar las credenciales del usuario
        local_common = xmlrpc.client.ServerProxy(f'{odoo_connection["url"]}/xmlrpc/2/common')
        user_uid = local_common.authenticate(odoo_connection['db'], usuario, clave, {})

        if user_uid:
            print("INFO: Autenticación exitosa.")
            # Guardar sesión exitosa
            odoo_connection['current_user_email'] = usuario # Guardamos el email del usuario actual
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump({'last_user': usuario, 'last_pass': clave}, f)
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo guardar el archivo de sesión: {e}")
            
            # Avanzar al siguiente formulario
            abrir_formulario_grupo()
        else:
            form_login.lblMensaje.setText("Error de autenticación. Verifique sus credenciales.")
            # Borrar config si las credenciales guardadas fallaron
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)

    except xmlrpc.client.ProtocolError as err:
        # Error específico de conexión (ej. URL incorrecta, servidor no responde)
        show_error_message("Error de Conexión", f"No se pudo conectar a Odoo en la URL:\n{odoo_connection['url']}\n\nVerifique la conexión de red o la configuración del servidor.", detailed_text=str(err))
        form_login.lblMensaje.setText("Error de conexión con Odoo.")

def toggle_password_visibility():
    """Cambia la visibilidad del campo de la contraseña en el formulario de login."""
    if form_login.txtClave.echoMode() == QLineEdit.EchoMode.Password:
        form_login.txtClave.setEchoMode(QLineEdit.EchoMode.Normal)
        form_login.btnMostrarClave.setText("Ocultar")
    else:
        form_login.txtClave.setEchoMode(QLineEdit.EchoMode.Password)
        form_login.btnMostrarClave.setText("Ver")

def on_click_cerrar_sesion():
    """Cierra la sesión actual, borra el archivo de config y vuelve a la pantalla de login."""
    print("INFO: Cerrando sesión.")
    # Borrar el archivo de configuración para olvidar al usuario
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("INFO: Archivo de sesión eliminado.")
    # Cerrar la ventana de grupo y mostrar la de login
    form_grupo.close()
    form_login.show()

def show_material_base_section():
    """Hace visible la sección de material base y intenta cargar los datos."""
    form_odoo.groupBox_MaterialBase.setVisible(True)
    # Obtenemos el ID del producto que se guardó en una propiedad del botón
    product_id = form_odoo.btnMostrarMaterialBase.property("product_id")
    get_material_base_from_inventor_integrado(product_id)


def run_app(inventor_instance):
    global inv, invApp, invDoc, app, form_login, form_grupo, form_odoo, form, formLM, odoo_connection, categorias_3

    inv = inventor_instance
    invApp = inventor_instance
    invDoc = invApp.ActiveDocument

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    # Cargar todos los formularios
    form_login = uic.loadUi(FORM_LOGIN_UI)
    form_grupo = uic.loadUi(FORM_GRUPO_UI)
    form_odoo = uic.loadUi(FORM_ODOO_UI)
    form_odoo.lblMensaje_5.setText("Autodesk Inventor tiene un documento activo.")
    form_odoo.ComboBoxDescripcion.clear()

    odoo_connection = {
        "url": 'http://192.168.10.13:8069',
        "db": 'PruebaCFReA',
        "user": 'it@automate-corp.com', # Usuario admin para operaciones
        "pass": 'Auto1234-',
        "uid": None,
        "models": None
    }

    # Ocultar la sección de material base al inicio
    form_odoo.groupBox_MaterialBase.setVisible(False)

    # La conexión inicial se moverá al login para manejar errores allí.
    # Aquí solo preparamos el diccionario.
    common = xmlrpc.client.ServerProxy(f'{odoo_connection["url"]}/xmlrpc/2/common')
    odoo_connection['uid'] = common.authenticate(odoo_connection['db'], odoo_connection['user'], odoo_connection['pass'], {})
    odoo_connection['models'] = xmlrpc.client.ServerProxy(f'{odoo_connection["url"]}/xmlrpc/2/object')

    def obtener_descripciones_categorias_3():
        if not odoo_connection or not odoo_connection.get('models'): return []
        conn = odoo_connection
        categorias_3 = conn['models'].execute_kw(conn['db'], conn['uid'], conn['pass'], 'x_categoria_3', 'search_read', [], {'fields': ['id', 'x_name', 'x_descripcion']})
        return categorias_3

    def correr_progrma_clases():
        form_odoo.ComboBoxDescripcion.clear()
        # --- INICIO DE LA MODIFICACIÓN ---
        if categorias_3 is not None and len(categorias_3) > 0:
            # 1. Ordenar la lista de categorías alfabéticamente por el 'x_name'
            categorias_3.sort(key=lambda cat: cat.get('x_name', ''))

            for categoria in categorias_3:
                descripcion = categoria.get('x_name', '')
                form_odoo.ComboBoxDescripcion.addItem(descripcion)

            # 2. Configurar el autocompletado con filtro
            completer = QCompleter(form_odoo.ComboBoxDescripcion.model(), form_odoo.ComboBoxDescripcion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains) # Filtra por contenido
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive) # No distingue mayúsculas/minúsculas
            form_odoo.ComboBoxDescripcion.setCompleter(completer)

            form_odoo.ComboBoxDescripcion.currentIndexChanged.connect(actualizar_labels_desde_combobox)
        # --- FIN DE LA MODIFICACIÓN ---

    categorias_3 = obtener_descripciones_categorias_3()
    # Ordenamos la lista principal de diccionarios para que el índice coincida con la lista ordenada del ComboBox
    if categorias_3:
        categorias_3.sort(key=lambda cat: cat.get('x_name', ''))
    correr_progrma_clases()

    # --- Conexiones de los formularios ---
    form_login.btnIniciarSesion.clicked.connect(on_click_iniciar_sesion)
    form_login.btnMostrarClave.clicked.connect(toggle_password_visibility)
    form_login.btnCerrarApp.clicked.connect(on_clickCerrar)
    
    # --- INICIO DE LA MODIFICACIÓN ---
    # Conectamos los nuevos botones a la nueva función manejadora
    form_grupo.btnGrupoMateriaPrimaEnsamble.clicked.connect(on_grupo_button_clicked)
    form_grupo.btnGrupoPreEnsambles.clicked.connect(on_grupo_button_clicked)
    form_grupo.btnGrupoMateriaPrimaProcesada.clicked.connect(on_grupo_button_clicked)
    # --- FIN DE LA MODIFICACIÓN ---
    form_grupo.btnCerrarSesion.clicked.connect(on_click_cerrar_sesion) # <-- NUEVA CONEXIÓN
    
    # --- INICIO DE LA MODIFICACIÓN DE INTEGRACIÓN ---
    # El botón 730 mantiene su funcionalidad original de abrir una ventana separada
    form_odoo.btn650.clicked.connect(abrir_formulario_650)
    form_odoo.btn730.clicked.connect(abrir_formulario_730)
    # El nuevo botón para mostrar la sección integrada
    form_odoo.btnMostrarMaterialBase.clicked.connect(show_material_base_section)
    # Conexiones para los botones dentro de la sección integrada
    form_odoo.btnValidar_integrado.clicked.connect(on_click_validar_integrado)
    # Usamos una lambda para pasar el ID del producto al crear la BoM
    form_odoo.btnCargar_integrado.clicked.connect(
        lambda: create_bom_for_product_integrado(form_odoo.btnMostrarMaterialBase.property("product_id"))
    )
    # --- FIN DE LA MODIFICACIÓN DE INTEGRACIÓN ---

    form_odoo.btnCerrarPrin.clicked.connect(on_clickCerrar)
    form_odoo.btnEnviar.clicked.connect(lambda: on_click(form_odoo.txtCodigo.text()))
    form_odoo.btnValidar.clicked.connect(on_click_validar)
    form_odoo.btnAbrirFormularioGrupo.clicked.connect(abrir_formulario_grupo)
    
    # Inicia mostrando el formulario de LOGIN
    form_login.show()
    load_session_config() # Intentar autologin

    sys.exit(app.exec())

def abrir_formulario_650():
    # Pasa la instancia 'inv' y la app existente al otro módulo
    import ListaDeMateriales
    # Obtenemos el ID del producto que se guardó en la propiedad del botón
    product_id = form_odoo.btn650.property("product_id")
    ListaDeMateriales.run_lista_materiales(inv, app, product_id)
    form_odoo.close() # Cierra el formulario principal
    

def abrir_formulario_730(product_id=None):
    # Esta función ahora solo se usa para el botón 730 original (casos de piezas ya existentes)
    # Pasa la instancia 'inv' y la app existente al otro módulo
    import LanzarMaterialBase1
    # --- CORRECCIÓN MODO REAL ---
    # No creamos un nuevo documento. El flujo debe continuar con el documento
    # activo actual, que es de donde se leerá la iProperty "Codigo Sizfra".
    # Pasamos el ID del producto recién creado.
    # Si product_id es None, significa que venimos del botón 730 y debemos buscar el ID.
    LanzarMaterialBase1.run_material_base(inv, app, product_id if product_id else obtener_id_product())
    form_odoo.close() # Cierra el formulario principal
