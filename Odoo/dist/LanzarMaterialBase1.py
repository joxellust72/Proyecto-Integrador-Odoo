import sys
import win32com.client as win32
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.uic import loadUi
import xmlrpc.client


# --- Variables Globales ---
inv = None
app = None
form = None
models = None
uid = None
odoo_db = None
odoo_pass = None


# Configuración de conexión a Odoo
odoo_url = 'http://192.168.10.13:8069'

ODDO_DB_NAME = 'PruebaCFReA'
ODOO_USER = 'it@automate-corp.com'
ODOO_PASS = 'Auto1234-'

def get_material_base_from_inventor():
    """
    Lee la iProperty 'Codigo Sizfra' de Inventor, busca el producto en Odoo
    y actualiza el formulario.
    """
    try:
        # 1. Leer la iProperty personalizada "Codigo Sizfra" de Inventor
        custom_props = inv.ActiveDocument.PropertySets.Item("User Defined Properties")
        codigo_sizfra = custom_props.Item("Codigo Sizfra").Value

        if not codigo_sizfra:
            form.lblMensaje.setText("Error: La propiedad 'Codigo Sizfra' está vacía en Inventor.")
            QMessageBox.critical(form, "Error", "La iProperty 'Codigo Sizfra' no puede estar vacía en el documento de Inventor.")
            return False

        # 2. Buscar el producto en Odoo usando el código como barcode
        product_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search_read',
                                       [[['barcode', '=', codigo_sizfra]]],
                                       {'fields': ['id', 'name'], 'limit': 1})

        if not product_ids:
            form.lblMensaje.setText(f"Error: No se encontró un producto en Odoo con el código: {codigo_sizfra}")
            QMessageBox.critical(form, "Error", f"No se encontró ningún material base en Odoo con el 'Codigo Sizfra': {codigo_sizfra}")
            return False

        # 3. Actualizar el formulario con el producto encontrado
        product_name = product_ids[0]['name']
        # Rellenamos el nuevo campo de texto. Es editable por si el usuario quiere cambiarlo.
        form.txtMaterialBase.setText(codigo_sizfra)
        form.lblMensaje.setText(f"Material base '{product_name}' (código: {codigo_sizfra}) cargado desde Inventor.")
        return True

    except Exception as e:
        error_msg = f"No se pudo leer la propiedad 'Codigo Sizfra' de Inventor. Asegúrese de que exista. Error: {e}"
        print(f"ERROR: {error_msg}")
        form.lblMensaje.setText("Error al leer la propiedad de Inventor.")
        QMessageBox.critical(form, "Error de Inventor", error_msg)
        return False

def obtener_id_product():
    #Extracion del valor del campo directamente del formualrio
    if not inv: return None
    # --- CORRECCIÓN DEL ERROR ---
    # El Part Number (barcode) aún no existe en Odoo en este punto.
    # Buscamos por el nombre (Title), que sí está definido en el mock.
    nomsis = inv.ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Title").Value
    
    # Búsqueda más segura que no causa IndexError
    product_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'search', [[['name', '=', nomsis]]], {'limit': 1})
    
    if product_ids:
        return product_ids[0]
    else:
        # Si no se encuentra, informamos al usuario y evitamos el crash.
        QMessageBox.critical(form, "Error", f"No se pudo encontrar el producto padre '{nomsis}' en Odoo para crear la lista de materiales.")
        return None
  
def obtener_variable_ideMaterial():
    # Ahora leemos el código directamente del campo de texto
    CodigoMaterialBase = str(form.txtMaterialBase.text())
    return CodigoMaterialBase

def obtener_id_material_base():
    CodigoMaterialBase = obtener_variable_ideMaterial()
    if not models: return None    
    search_result = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search', [[['barcode', '=', CodigoMaterialBase]]], {'limit': 1})
    if search_result:
        return search_result[0] # Devuelve el primer ID encontrado
    else:
        return None # Devuelve None si no se encontró nada

def API_Autodesk_Inventor_imput():    
    NombreMaterialbase = obtener_variable_ideMaterial()
    try:
        part = inv.ActiveDocument.ComponentDefinition         
        personalizada_material_base = part.Document.PropertySets.Item("User Defined Properties").Item("Material Base")
        # Buscamos el nombre del producto para guardarlo en la iProperty
        product_name = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'read', [obtener_id_material_base()], {'fields': ['name']})[0]['name']
        nueva_material_base = product_name
        nueva_material_base = NombreMaterialbase.lower()
        personalizada_material_base.Value = nueva_material_base 
        print("Se ha establecido el material base de la pieza en Autodesk Inventor:", nueva_material_base)  
        inv.ActiveDocument.Save()
    except Exception as e:
        print("Error: ", e)
        print("El documento activo no es un archivo de pieza (part).")   
    
def obtener_id_lista_materiales_cargada():
    product_ids = obtener_id_product()
    product_tmpl_id = product_ids 
    vals = [{'product_tmpl_id': product_tmpl_id, 'product_qty':1}]
    listacreada = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom', 'create',[vals])[0]
    return listacreada

def obtener_unidad_material_base():
    if not models: return "" 
    material_base_ids_prod = obtener_id_material_base()
    # --- INICIO DE LA CORRECCIÓN ---
    # Añadimos una comprobación para asegurarnos de que tenemos un ID antes de consultar a Odoo.
    if not material_base_ids_prod:
        return "" # Si no hay ID, devolvemos una cadena vacía y evitamos el error. 
    product_datauom = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'read', [material_base_ids_prod], {'fields': ['uom_id']})  
    uom_id = product_datauom[0]['uom_id']   
    uom_data = models.execute_kw(odoo_db, uid, odoo_pass, 'uom.uom', 'read', [uom_id[0]], {'fields': ['name']})  
    uom_data1 = uom_data[0]['name']          
    return uom_data1 

def obtener_id_lista_unidades_odoo():
    uom_data1 = obtener_unidad_material_base()  
    if not models: return ""  
    # Buscar el ID de la unidad de medida
    uom_id = str(models.execute_kw(odoo_db, uid, odoo_pass, 'uom.uom', 'search', [[('name', '=', uom_data1)]])[0])
    return uom_id
    
def obtener_cantidad_material_base():
    if not inv: return 0
    uom_data1 = obtener_unidad_material_base()
    if uom_data1 == "kg":
        mass = str(round(inv.ActiveDocument.PropertySets.Item("Design Tracking Properties").Item("Mass").Value/1000,2))
        mass_in_kg_str = mass +" kg"
        ValueOdoo = float(mass)
        print(f"vista: {ValueOdoo}")
        form.txtCantReq.setText(str(mass_in_kg_str))
        form.txtCantReq.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        return ValueOdoo
    else:
        ValueOdooForm = inv.ActiveDocument.ComponentDefinition.BOMQuantity.UnitQuantity
        if ValueOdooForm == "":
            ValueOdoo = 1
            form.txtCantReq.setText(str("1 Uni"))
            form.txtCantReq.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        else:
            ValueOdoo = float(ValueOdooForm.split(" ")[0]) 
            form.txtCantReq.setText(str(ValueOdooForm))
            form.txtCantReq.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura           
        if ValueOdoo:
            print(f"Unit Quantity: {ValueOdoo}")
            return ValueOdoo
        else:
            ValueOdoo = 1
            print(ValueOdoo)

def on_click_validar():
        obtener_id_product()      
        obtener_variable_ideMaterial()           
        obtener_cantidad_material_base()  

def create_bom_for_product():                    
    material_base_ids_prod = obtener_id_material_base()
    listacreada = obtener_id_lista_materiales_cargada()
    uom_id = obtener_id_lista_unidades_odoo()
    ValueOdoo = obtener_cantidad_material_base()       
    print(listacreada)
    print(material_base_ids_prod)
    print(ValueOdoo)
    print(uom_id) 
    vals = [{'bom_id': listacreada, 'product_id': material_base_ids_prod, 'product_qty':ValueOdoo, 'product_uom_id':uom_id}]
    listacargada = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom.line', 'create',[vals])
    print(listacargada)
    API_Autodesk_Inventor_imput()
    form.lblMensaje.setText(f"Lista cargada con exito con ID: {listacargada}")
    form.btnConfiMateBase.setStyleSheet("background-color: blue; color: white;")

def arranque_codigo():
    global form
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FORM_MATERIAL_BASE_UI = os.path.join(BASE_DIR, "FormularioMaterialBase.ui")
    form = loadUi(FORM_MATERIAL_BASE_UI)

    nomsis = inv.ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Title").Value
    form.txtProductoPadre.setText(nomsis)
    form.txtProductoPadre.setReadOnly(True)

    form.show()
    # Ahora llamamos a la nueva función para que cargue el material automáticamente
    get_material_base_from_inventor()

def on_clickCerrar():
    if form:
        form.close()
    if app:
        app.quit()

def run_material_base(inventor_instance, q_application):
    """Función principal para lanzar este formulario."""
    global inv, app, form, models, uid, odoo_db, odoo_pass

    inv = inventor_instance
    app = q_application
    odoo_db = ODDO_DB_NAME
    odoo_pass = ODOO_PASS

    try:
        common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
        uid = common.authenticate(odoo_db, ODOO_USER, odoo_pass, {})
        models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
    except Exception as e:
        QMessageBox.critical(None, "Error de Odoo", f"No se pudo conectar a Odoo: {e}")
        return

    arranque_codigo()
    # La carga ahora es automática, el usuario solo necesita validar y confirmar.
    form.lblMensaje.setText("Material base cargado desde Inventor. Valide y confirme.")
    form.btnValidar.clicked.connect(on_click_validar)
    form.btnConfiMateBase.clicked.connect(create_bom_for_product)
    form.btnCerrar.clicked.connect(on_clickCerrar)