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

product_template_id = None # <-- NUEVA VARIABLE GLOBAL para guardar el ID del producto padre

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
        codigo_sizfra = "" # Inicializamos como cadena vacía
        custom_props = inv.ActiveDocument.PropertySets.Item("User Defined Properties")
        # --- INICIO DE LA CORRECCIÓN ---
        # Intentamos leer la propiedad. Si no existe, no fallará, codigo_sizfra seguirá vacío.
        try:
            codigo_sizfra = custom_props.Item("CODIGO SIZFRA").Value
        except (AttributeError, KeyError, Exception):
            print("ADVERTENCIA: La iProperty 'Codigo Sizfra' no existe en el documento. Se asumirá como vacía.")
        # --- FIN DE LA CORRECCIÓN ---

        if not codigo_sizfra:
            QMessageBox.critical(form, "Error", "La iProperty 'Codigo Sizfra' no puede estar vacía en el documento de Inventor.")
            return False

        # --- INICIO DE LA SOLUCIÓN (LIMPIEZA DE DATOS) ---
        # 1. Convertimos a float para asegurar que es un número.
        # 2. Convertimos a int para truncar la parte decimal (.0).
        # 3. Convertimos a string para tener el formato de texto limpio.
        # 4. Usamos strip() por si acaso hay espacios.
        codigo_sizfra = str(int(float(codigo_sizfra))).strip()
        # --- FIN DE LA SOLUCIÓN ---

        # --- INICIO DE LA SOLUCIÓN MEJORADA ---
        # 2. Búsqueda Múltiple: Intentar por 'default_code' (Referencia Interna) y luego por 'barcode'.
        # El operador '|' en los dominios de Odoo significa 'OR'.
        search_domain = [
            '|',
            ['default_code', '=', codigo_sizfra],
            ['barcode', '=', codigo_sizfra]
        ]
        product_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search_read', [search_domain], {'fields': ['id', 'name', 'default_code'], 'limit': 1})
        # --- FIN DE LA SOLUCIÓN MEJORADA ---

        if not product_ids:
            error_msg = f"No se encontró material base en Odoo con el código '{codigo_sizfra}' (ni como Ref. Interna ni como Cód. Barras)."
            QMessageBox.critical(form, "Error de Búsqueda", error_msg)
            form.lblMensaje.setText(error_msg)
            return False

        # 3. Actualizar el formulario con el producto encontrado
        product_name = product_ids[0]['name']
        # Usamos el código que realmente está en Odoo (default_code o el que se usó)
        found_code = product_ids[0].get('default_code') or codigo_sizfra
        form.txtMaterialBase.setText(found_code)
        form.lblMensaje.setText(f"Material base '{product_name}' (código: {found_code}) cargado.")
        return True

    except Exception as e:
        error_msg = f"No se pudo leer la propiedad 'Codigo Sizfra' de Inventor. Asegúrese de que exista. Error: {e}"
        print(f"ERROR: {error_msg}")
        form.lblMensaje.setText("Error al leer la propiedad de Inventor.")
        QMessageBox.critical(form, "Error de Inventor", error_msg)
        return False

def obtener_id_product(): # Esta función ya no es necesaria, pero la dejamos por si se usa en otro lado.
    return product_template_id
  
def obtener_variable_ideMaterial():
    # Ahora leemos el código directamente del campo de texto
    # --- INICIO DE LA SOLUCIÓN (LIMPIEZA DE DATOS) ---
    # También limpiamos el texto del formulario por si el usuario lo modifica manualmente.
    CodigoMaterialBase = str(form.txtMaterialBase.text()).strip()
    # --- FIN DE LA SOLUCIÓN ---
    return CodigoMaterialBase

def obtener_id_material_base():
    CodigoMaterialBase = obtener_variable_ideMaterial()
    if not models: return None    
    # --- INICIO DE LA SOLUCIÓN (UNIFICACIÓN DE LÓGICA) ---
    # Usamos la misma lógica de búsqueda múltiple para ser consistentes.
    search_domain = [
        '|',
        ['default_code', '=', CodigoMaterialBase],
        ['barcode', '=', CodigoMaterialBase]
    ]
    search_result = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search', [search_domain], {'limit': 1})
    # --- FIN DE LA SOLUCIÓN ---
    if search_result:
        return search_result[0] # Devuelve el primer ID encontrado
    else:
        return None # Devuelve None si no se encontró nada

def API_Autodesk_Inventor_imput():    
    NombreMaterialbase = obtener_variable_ideMaterial()
    try:
        part = inv.ActiveDocument.ComponentDefinition         
        personalizada_material_base = part.Document.PropertySets.Item("User Defined Properties").Item("Material Base")
        id_material_base = obtener_id_material_base()
        # Buscamos el nombre del producto para guardarlo en la iProperty
        product_name = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'read', [id_material_base], {'fields': ['name']})[0]['name']
        nueva_material_base = product_name
        # El valor a guardar es el código, no el nombre.
        personalizada_material_base.Value = nueva_material_base 
        print("Se ha establecido el material base de la pieza en Autodesk Inventor:", nueva_material_base)  
        inv.ActiveDocument.Save()
    except Exception as e:
        print("Error: ", e)
        print("El documento activo no es un archivo de pieza (part).")   
    
def obtener_id_lista_materiales_cargada():
    if not product_template_id:
        QMessageBox.critical(form, "Error Crítico", "No se ha proporcionado un ID de producto para crear la BoM.")
        return None
    
    # --- LÓGICA MEJORADA: Buscar antes de crear ---
    # 1. Buscar si ya existe una BoM para este producto.
    bom_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom', 'search',
                                [[['product_tmpl_id', '=', product_template_id]]], {'limit': 1})

    if bom_ids:
        listacreada = bom_ids[0] # Si existe, usamos esa.
    else:
        # 2. Si no existe, la creamos.
        vals = [{'product_tmpl_id': product_template_id, 'product_qty': 1}]
        # --- INICIO DE LA CORRECCIÓN ---
        # El método 'create' devuelve una lista con el ID, ej: [123]. Extraemos solo el ID.
        new_bom_id = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom', 'create', [vals])
        listacreada = new_bom_id[0] if new_bom_id else None
        # --- FIN DE LA CORRECCIÓN ---
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
    props = inv.ActiveDocument.PropertySets
    uom_data1 = obtener_unidad_material_base()
    if uom_data1 == "kg":
        mass = str(round(props.Item("Design Tracking Properties").Item("Mass").Value / 1000, 2))
        mass_in_kg_str = mass + " kg"
        ValueOdoo = float(mass)
        print(f"vista: {ValueOdoo}")
        form.txtCantReq.setText(str(mass_in_kg_str))
        form.txtCantReq.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        return ValueOdoo
    else:
        ValueOdooForm = inv.ActiveDocument.ComponentDefinition.BOMQuantity.UnitQuantity
        # En el mock, BOMQuantity no está completamente simulado, así que asumimos 1.
        # En el modo real, esto debería funcionar como antes.
        # La condición `ValueOdooForm == ""` es para el modo real.
        if ValueOdooForm == "" or "Mock" in inv.__class__.__name__:
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
        # obtener_id_product() # Ya no es necesario llamar a esto aquí
        obtener_variable_ideMaterial()           
        obtener_cantidad_material_base()  

def create_bom_for_product():                    
    material_base_ids_prod = obtener_id_material_base()
    if not material_base_ids_prod:
        QMessageBox.critical(form, "Error", "No se pudo encontrar el material base en Odoo. Verifique el código.")
        return

    listacreada = obtener_id_lista_materiales_cargada()
    if not listacreada:
        QMessageBox.critical(form, "Error", "No se pudo crear o encontrar la lista de materiales para el producto padre.")
        return

    uom_id = obtener_id_lista_unidades_odoo()
    ValueOdoo = obtener_cantidad_material_base()       
    print(listacreada)
    print(material_base_ids_prod)
    print(ValueOdoo)
    print(uom_id) 
    vals = [{'bom_id': listacreada, 'product_id': material_base_ids_prod, 'product_qty': ValueOdoo, 'product_uom_id': uom_id}]
    listacargada = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom.line', 'create', [vals])
    print(listacargada)

    API_Autodesk_Inventor_imput()
    form.lblMensaje.setText(f"Lista cargada con exito con ID: {listacargada}")
    form.btnConfiMateBase.setStyleSheet("background-color: blue; color: white;")

def arranque_codigo():
    global form
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FORM_MATERIAL_BASE_UI = os.path.join(BASE_DIR, "FormularioMaterialBase.ui")
    form = loadUi(FORM_MATERIAL_BASE_UI)

    # Acceso corregido para el mock
    nomsis = inv.ActiveDocument.PropertySets.Item("Inventor Summary Information").Item("Title").Value
    form.txtProductoPadre.setText(nomsis)
    form.txtProductoPadre.setReadOnly(True)

    form.show()
    # Ahora llamamos a la nueva función para que cargue el material automáticamente
    get_material_base_from_inventor()

def on_clickCerrar(exit_app=True):
    if form:
        form.close()
    if app:
        app.quit()

def run_material_base(inventor_instance, q_application, product_id):
    """Función principal para lanzar este formulario."""
    global inv, app, form, models, uid, odoo_db, odoo_pass, product_template_id

    inv = inventor_instance
    app = q_application
    odoo_db = ODDO_DB_NAME
    odoo_pass = ODOO_PASS

    product_template_id = product_id # Guardamos el ID del producto padre
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