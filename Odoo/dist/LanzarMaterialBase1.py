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

# Función para cargar datos de productos desde Odoo
def load_product_data():
    if not models: return []
    # Filtrar los productos por categoría
    category_name = 'MATERIA PRIMA FABRICACION'
    domain = [('categ_id.name', '=', category_name)]
    # Buscar registros de productos que cumplan con el filtro
    product_template_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'search', [domain])
    # Obtener los datos de los productos basados en los IDs
    product_data = get_product_data(product_template_ids)
    return product_data

# Función para obtener los datos de los productos
def get_product_data(product_template_ids):
    product_data = []
    if not models: return product_data
    for product_id in product_template_ids:
        product = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'read', [product_id], {'fields': ['id', 'name']})
        product_data.append((product[0]['id'], product[0]['name']))
    return product_data

# Función para actualizar la lista de productos en el formulario
def update_product_list():
    product_data = load_product_data()
    form.ComboBoxMaterialBase.clear()  # Limpiar el cuadro combinado
    product_names = [product[1] for product in product_data]
    form.ComboBoxMaterialBase.addItems(product_names)  # Poblar el cuadro combinado con los nuevos datos

# Función para cargar una lista predefinida de productos
def get_product_of_list():
    listaPrecargada = [(54206, 'ANGULO ACERO 1 1/4" X 3/16"'), (54203, 'ANGULO ACERO 1 1/4" x 1/8'), (54201, 'ANGULO ACERO 2 1/2 " x 3/16'), 
                    (54204, 'ANGULO ACERO 2" x 1/8'), (54202, 'ANGULO ACERO 2" x 3/16'), (54205, 'ANGULO ACERO 3/4 2.5'), (54195, 'ANGULO ALUMINIO 1" x 1/8"'), 
                    (54196, 'ANGULO ALUMINIO 1.1/2" x 3/16"'), (54194, 'ANGULO ALUMINIO 3/4" X 1/8"'), (54199, 'ANGULO INOXIDABLE 1/8 X 1'), (54200, 'ANGULO INOXIDABLE 1/8 X 3/4'), 
                    (54198, 'ANGULO INOXIDABLE 1/8" X 1 1/2"'), (54197, 'ANGULO INOXIDABLE 3/16" X 1 1/2"'), (54215, 'BANDA PLASTICA 10" CON EMPUJADOR 3" VER PLANO'), 
                    (54214, 'BANDA PLASTICA 12" CON EMPUJADOR 1" VER PLANO'), (54208, 'BANDA PLASTICA LISA ANCHO 10"'), (54207, 'BANDA PLASTICA LISA ANCHO 12"'), 
                    (54211, 'BANDA PLASTICA LISA ANCHO 15"'), (54209, 'BANDA PLASTICA LISA ANCHO 20"'), (54210, 'BANDA PLASTICA LISA ANCHO 30 MM'), (54212, 'BANDA PLASTICA LISA ANCHO 6"'), 
                    (54213, 'BANDA SIN FIN 1416MM'), (56656, 'BANDA VM2 DE 1452MM X 400MM UNIDA CON CHAVETAS INOXIDABLE'), (54424, 'BANDEJA METÁLICA PORTACABLES CF54X100MM'), 
                    (54423, 'BANDEJA METÁLICA PORTACABLES CF54X150mm'), (54338, 'BARRA CUADRADA AISI 1020 2"'), (54335, 'BARRA CUADRADA INOXIDABLE 1 1/2"'), 
                    (54336, 'BARRA CUADRADA INOXIDABLE 1"'), (54337, 'BARRA CUADRADA INOXIDABLE 1/2"'), (54453, 'BARRA REDONDA INOXIDABLE 2 1/2"'), (54452, 'BARRA REDONDA INOXIDABLE 3/4 "'),
                      (54287, 'BARRA ROSCADA GALVANIZADA 1/4'), (54288, 'BARRA ROSCADA GALVANIZADA 3/4'), (54289, 'BARRA ROSCADA GALVANIZADA 5/8'), (54285, 'BARRA ROSCADA GALVANIZADA M12'), 
                      (54286, 'BARRA ROSCADA GALVANIZADA M16'), (54284, 'BARRA ROSCADA GALVANIZADA M6'), (54296, 'BARRA ROSCADA INOXIDABLE 1/2'), (54295, 'BARRA ROSCADA INOXIDABLE 1/4'), 
                      (54294, 'BARRA ROSCADA INOXIDABLE 3/8'), (54292, 'BARRA ROSCADA INOXIDABLE M12'), (54290, 'BARRA ROSCADA INOXIDABLE M16'), (54291, 'BARRA ROSCADA INOXIDABLE M6'), 
                      (54293, 'BARRA ROSCADA INOXIDABLE M8'), (54283, 'BARRA ROSCADA NEGRA 1"'), (54282, 'BARRA ROSCADA NEGRA M6'), (54408, 'CABLE # 10 THHN'), (54409, 'CABLE # 12 THHN'), 
                      (54411, 'CABLE # 4 THHN'), (54410, 'CABLE # 4/0 THHN'), (54406, 'CABLE # 6 THHN'), (54407, 'CABLE # 8 THHN'), (54362, 'CABLE CONTROL 10X22'), 
                      (54348, 'CABLE CONTROL 16X22'), (54350, 'CABLE CONTROL 20X20'), (54361, 'CABLE CONTROL 25X22'), (54349, 'CABLE CONTROL 2X20'), (54354, 'CABLE CONTROL 2X22'), 
                      (54366, 'CABLE CONTROL 3X18'), (54351, 'CABLE CONTROL 3X20'), (54360, 'CABLE CONTROL 3X22'), (54404, 'CABLE CONTROL 4X20'), (54359, 'CABLE CONTROL 4X22'), 
                      (54364, 'CABLE CONTROL 5 X 22'), (54365, 'CABLE CONTROL 6X18'), (54363, 'CABLE CONTROL 6X22'), (54368, 'CABLE CONTROL 7X22'), (54356, 'CABLE CONTROL 8X24'), 
                      (54405, 'CABLE DESNUDO # 4 THHN'), (54375, 'CABLE ENCAUCHETADO 2 X 18'), (54374, 'CABLE ENCAUCHETADO 3 X 10'), (54372, 'CABLE ENCAUCHETADO 3 X 14'), 
                      (54370, 'CABLE ENCAUCHETADO 3 X 18'), (54373, 'CABLE ENCAUCHETADO 3 X 8'), (54380, 'CABLE ENCAUCHETADO 3X12'), (54381, 'CABLE ENCAUCHETADO 3X16'), 
                      (54377, 'CABLE ENCAUCHETADO 4 X 10'), (54371, 'CABLE ENCAUCHETADO 4 X 14'), (54376, 'CABLE ENCAUCHETADO 4 X 16'), (54369, 'CABLE ENCAUCHETADO 4 X 18'), 
                      (54378, 'CABLE ENCAUCHETADO 4 X 6'), (54379, 'CABLE ENCAUCHETADO 4 X 8'), (54352, 'CABLE ENCAUCHETADO 7 X 22'), (54358, 'CABLE RIBBON 26'), (54355, 'CABLE RIBBON 40'),
                       (54367, 'CABLE UTP CAT 6 APANTALLADO'), (54357, 'CABLE UTP5'), (54353, 'CABLE UTP6'), (54385, 'CABLE VEHICULAR AMARILLO CAL 18'), 
                       (54401, 'CABLE VEHICULAR AMARILLO CAL 20'), (54394, 'CABLE VEHICULAR AZUL CAL 14'), (54398, 'CABLE VEHICULAR AZUL CAL 16'), (54388, 'CABLE VEHICULAR AZUL CAL 18'), 
                       (54383, 'CABLE VEHICULAR AZUL CAL 20'), (54390, 'CABLE VEHICULAR AZUL CAL 22'), (54389, 'CABLE VEHICULAR AZUL CAL 24'), (54396, 'CABLE VEHICULAR BLANCO CAL 14'), 
                       (54384, 'CABLE VEHICULAR BLANCO CAL 20'), (54391, 'CABLE VEHICULAR BLANCO CAL 22'), (54403, 'CABLE VEHICULAR GRIS CAL 16'), (54382, 'CABLE VEHICULAR NEGRO CAL 14'), 
                       (54387, 'CABLE VEHICULAR NEGRO CAL 16'), (54402, 'CABLE VEHICULAR NEGRO CAL 20'), (54395, 'CABLE VEHICULAR ROJO CAL 14'), (54399, 'CABLE VEHICULAR ROJO CAL 16'), 
                       (54400, 'CABLE VEHICULAR ROJO CAL 18'), (54393, 'CABLE VEHICULAR VERDE CAL 12'), (54386, 'CABLE VEHICULAR VERDE CAL 14'), (54397, 'CABLE VEHICULAR VERDE CAL 16'), 
                       (54392, 'CABLE VEHICULAR VERDE CAL 20'), (54184, 'CADENA DE TRANSMISION CHJC 40-1'), (54185, 'CADENA DE TRANSMISION TRP 40-1'), 
                       (54186, 'CADENA DE TRANSMISION TRP 50-1'), (54187, 'CADENA DE TRANSMISIÓN TRP 50-1'), (54347, 'CADENA PORTA CABLES DE PLASTICO R38 15X40'), 
                       (54346, 'CADENA PORTA CABLES DE PLASTICO R55 30X38'), (54223, 'CANAL C 3" X 4.1 LB-FT'), (54222, 'CANAL EN U'), (54419, 'CANALETA METALICA 20X8 GALCO'), 
                       (54412, 'CANALETA RANURADA 25X25'), (54413, 'CANALETA RANURADA 25X40'), (54418, 'CANALETA RANURADA 25X60'), (54414, 'CANALETA RANURADA 40X40'), 
                       (54417, 'CANALETA RANURADA 40X60'), (54415, 'CANALETA RANURADA 60X60'), (54416, 'CANALETA RANURADA 60x40'), (54327, 'CONECTOR EMT 1"'), (54421, 'CORAZA METALICA 1"'),
                         (54422, 'CORAZA METALICA 1/2'), (54420, 'CORAZA METALICA 3/4'), (54191, 'CORREA DENTADA CAUCHO'), (54193, 'CORREA DENTADA L100'), 
                         (54192, 'CORREA DENTADA PLASTICA H100'), (54190, 'CORREA DENTADA PLASTICA H150'), (54188, 'CORREA DENTADA PLASTICA L050'), (54189, 'CORREA DENTADA PLASTICA L075'), 
                         (54326, 'CURVA EMT 1"'), (54302, 'CUÑA ACERO 1/4'), (54301, 'CUÑA ACERO 3/8'), (54300, 'CUÑA ACERO M4'), (54299, 'CUÑA ACERO M5'), (54298, 'CUÑA ACERO M6'), 
                         (54297, 'CUÑA ACERO M8'), (54269, 'EJE METALICO MEDIA CAÑA 3MM X 80MM'), (54245, 'EJE REDODNDO INOXIDABLE 1/2'), (54276, 'EJE REDONDO 1016 ACERO 1/2"'), 
                         (54259, 'EJE REDONDO 1020 ACERO 1 1/2"'), (54262, 'EJE REDONDO 1020 ACERO 1"'), (54258, 'EJE REDONDO 1020 ACERO 1/2"'), (54264, 'EJE REDONDO 1020 ACERO 10MM'), 
                         (54266, 'EJE REDONDO 1020 ACERO 17MM'), (54263, 'EJE REDONDO 1020 ACERO 2"'), (54260, 'EJE REDONDO 1020 ACERO 3/4"'), (54261, 'EJE REDONDO 1020 ACERO 3/8"'),
                        (54267, 'EJE REDONDO 1020 ACERO 4"'), (54254, 'EJE REDONDO 1045 ACERO 1 1/2"'), (54255, 'EJE REDONDO 1045 ACERO 1 1/4"'), (54265, 'EJE REDONDO 1045 ACERO 1 1/8"'),
                        (54271, 'EJE REDONDO 1045 ACERO 1 3/4'), (54253, 'EJE REDONDO 1045 ACERO 1"'), (54268, 'EJE REDONDO 1045 ACERO 1/2"'), (54256, 'EJE REDONDO 1045 ACERO 2 1/2"'), 
                        (54270, 'EJE REDONDO 1045 ACERO 2 3/4'), (54273, 'EJE REDONDO 1045 ACERO 2"'), (54257, 'EJE REDONDO 1045 ACERO 3/4"'), (54275, 'EJE REDONDO 1045 ACERO 5/8"'), 
                        (54274, 'EJE REDONDO 1045 ACERO 7/8"'), (54251, 'EJE REDONDO 4140 ACERO 1 1/2"'), (54252, 'EJE REDONDO 4140 ACERO 1 1/4"'), (54272, 'EJE REDONDO 4140 ACERO 7/8"'),
                        (54228, 'EJE REDONDO ALUMINIO 1"'), (54233, 'EJE REDONDO ALUMINIO 2"'), (54230, 'EJE REDONDO ALUMINIO 2" 1/2'), (54231, 'EJE REDONDO ALUMINIO 2" 3/4'), 
                        (54226, 'EJE REDONDO ALUMINIO 3"'), (54229, 'EJE REDONDO ALUMINIO 3/4"'), (54227, 'EJE REDONDO ALUMINIO 4"'), (54234, 'EJE REDONDO ALUMINIO 5/8'), 
                        (54232, 'EJE REDONDO ALUMINIO 6"'), (54235, 'EJE REDONDO INOXIDABLE 1 1/2"'), (54246, 'EJE REDONDO INOXIDABLE 1 1/4"'), (54250, 'EJE REDONDO INOXIDABLE 1 3/4"'), 
                        (54239, 'EJE REDONDO INOXIDABLE 1"'), (54248, 'EJE REDONDO INOXIDABLE 1/4'), (54241, 'EJE REDONDO INOXIDABLE 2 1/2"'), (54247, 'EJE REDONDO INOXIDABLE 2"'), 
                        (54243, 'EJE REDONDO INOXIDABLE 20MM NIM20SS-0600-SL'), (54244, 'EJE REDONDO INOXIDABLE 25MM NIM20SS-0600-SL'), (54237, 'EJE REDONDO INOXIDABLE 3"'), 
                        (54238, 'EJE REDONDO INOXIDABLE 3/4"'), (54236, 'EJE REDONDO INOXIDABLE 3/8"'), (54242, 'EJE REDONDO INOXIDABLE 5/16"'), (54240, 'EJE REDONDO INOXIDABLE 5/8"'), 
                        (54426, 'ESPIRAL PLASTICO PORTACABLES 1"'), (54425, 'ESPIRAL PLASTICO PORTACABLES 1/2'), (54427, 'ESPIRAL PLÁSTICO PORTACABLES 3/8'), 
                        (54435, 'EXTRUSION ALUMINIO 1515-LS'), (54436, 'EXTRUSION ALUMINIO 1530-LS'), (54437, 'EXTRUSION ALUMINIO 1545 - LS'), (54438, 'EXTRUSION ALUMINIO 3030 - LS'), 
                        (54249, 'Eje redondo inoxidable 1/2"'), (54432, 'FILAMENTO PLASTICO NYLON - 3DXTECH'), (54433, 'FILAMENTO PLASTICO NYLON X'), (54434, 'FILAMENTO PLASTICO PET'), 
                        (54430, 'FILAMENTO PLASTICO PLA'), (54431, 'FILAMENTO PLASTICO TPU - HATCHBOX'), (54225, 'GUAYA DE SEGURIDAD ROJA 3/16'), (54161, 'LAMINA ALFAJOR ALUMINIO 2.9 MM'), 
                        (54164, 'LAMINA ALFAJOR ALUMINIO 3MM'), (54158, 'LAMINA ALUMINIO 10 MM'), (54159, 'LAMINA ALUMINIO 16 MM'), (54165, 'LAMINA ALUMINIO 20 MM'), 
                        (54160, 'LAMINA ALUMINIO 32 MM'), (54162, 'LAMINA ALUMINIO 3MM'), (54163, 'LAMINA ALUMINIO 6MM'), (54182, 'LAMINA CR CAL 14'), (54178, 'LAMINA CR CAL 18'), 
                        (54180, 'LAMINA HR 1/2'), (54175, 'LAMINA HR 1/4'), (54179, 'LAMINA HR 1/8'), (54174, 'LAMINA HR 18 MM'), (54173, 'LAMINA HR 25.00 MM'), (54176, 'LAMINA HR 3/16'), 
                        (54181, 'LAMINA HR 3/4"'), (54177, 'LAMINA HR 3/8'), (54168, 'LAMINA INOXIDABLE 1/4'), (54167, 'LAMINA INOXIDABLE 1/8"'), (54166, 'LAMINA INOXIDABLE 3/16'), 
                        (54170, 'LAMINA INOXIDABLE CAL 14'), (54169, 'LAMINA INOXIDABLE CAL 18'), (54450, 'LAMINA MDF 18MM'), (54171, 'LAMINA NYLON 20MM'), (54446, 'LAMINA OSB M11'), 
                        (54172, 'LAMINA PLASTICA PVC TRANSPARENTE'), (54183, 'LAMINA POLIETILENO HD'), (54448, 'LARGUERO PINO 1 X 2'), (54444, 'LARGUERO PINO 1 X 4'), 
                        (54449, 'LARGUERO PINO 1 X 6'), (54447, 'LARGUERO PINO 2 X 2'), (54445, 'LARGUERO PINO 2 X 4'), (54429, 'MANGUERA FLEXIBLE DE VACIO 1- 1/2 "'), 
                        (54328, 'MANGUERA PU 1/2'), (54334, 'MANGUERA PU 1/4'), (54331, 'MANGUERA PU 10MM'), (54333, 'MANGUERA PU 12MM'), (54332, 'MANGUERA PU 16 MM'), 
                        (54329, 'MANGUERA PU 3/8'), (54330, 'MANGUERA PU 8MM'), (54277, 'NYLON EJE REDONDO 1 1/2"'), (54278, 'NYLON EJE REDONDO 2"'), (54279, 'NYLON EJE REDONDO 3"'), 
                        (54343, 'PATIN LINEAL HGW20CC'), (54442, 'PERFIL DESGASTE PLANO'), (54440, 'PERFIL DESGASTE SOMBRILLA'), (54441, 'PERFIL DESGASTE TIPO U 41 MM (W534)'), 
                        (54439, 'PERFIL DESGASTE TIPO Z (W508)'), (54157, 'PERFIL HEA 100 ASTM A572 GR50'), (54443, 'PERFIL RANURADO 4X4X3'), (54220, 'PLATINA ACERO 1/2'), 
                        (54221, 'PLATINA ACERO 2" X 3/16"'), (54217, 'PLATINA ACERO INOXIDABLE 1/8" X 1"'), (54216, 'PLATINA ACERO INOXIDABLE 3/16" X 3/4"'), 
                        (54224, 'PLATINA ALUMINIO 3/4" X 3/16'), (54219, 'PLATINA DE HIERRO 1/4 X 1 1/2'), (54218, 'PLATINA HIERRO 1" x 1/8"'), (54281, 'POLIETILENO EJE REDONDO 1" U4'), 
                        (54280, 'POLIETILENO EJE REDONDO 2" UA'), (54339, 'RIEL 20MM ACERO PLATA'), (54428, 'RIEL DIN'), (54341, 'RIEL LINEAL HGR20R'), 
                        (54345, 'RIEL LINEAL HGR20R - 880 MM'), (54344, 'RIEL LINEAL HGR20R - 940MM'), (54342, 'RIEL LINEAL REDONDO 12mm'), (54340, 'RIEL LINEAL SBR20'),
                        (54455, 'TORRE ESTANTERIA'), (54318, 'TUBO CUADRADO ACERO 25 X 2'), (54307, 'TUBO CUADRADO INOX 1 1/2 CAL 14'), (54305, 'TUBO CUADRADO INOX 1 1/2 CAL 16'), 
                        (54306, 'TUBO CUADRADO INOX 1 1/4 CAL 14'), (54304, 'TUBO CUADRADO INOX 1 1/4 CAL 16'), (54319, 'TUBO CUADRADO PTS 100X100X2.0 MM'), 
                        (54313, 'TUBO CUADRADO PTS 30X30X2.0 MM'), (54317, 'TUBO CUADRADO PTS 40X40X2.0 MM'), (54312, 'TUBO CUADRADO PTS 50X50X2.0 MM'), 
                        (54309, 'TUBO CUADRADO PTS 60X60X2.0 MM'), (54314, 'TUBO CUADRADO PTS 60X60X2.5 MM'), (54311, 'TUBO CUADRADO PTS 90X90X2.0MM'), (54325, 'TUBO EMT 1"'), 
                        (54316, 'TUBO EST CUADRADO 50X50X3MM 6 MM'), (54315, 'TUBO EST CUADRADO100X100X4MM 6 MM'), (54323, 'TUBO RECTANCUGAR PTS 120X60X2.0MM'), 
                        (54321, 'TUBO RECTANCUGAR PTS 30X50X2.0MM'), (54322, 'TUBO RECTANGULAR PTS 100X50X2.0 MM'), (54320, 'TUBO RECTANGULAR PTS 90X50X2.0 MM'), 
                        (54308, 'TUBO REDONDO ACERO INOXIDABLE 1 1/4"'), (54303, 'TUBO REDONDO ALUMINIO 1 1/2"'), (54324, 'TUBO REDONDO NEGRO CR 2 X 2.5MM NTC-1560'), 
                        (54310, 'Tubo Cuadrado PTS 25X25X1.5 MM'), (54454, 'VIGA ESTANTERIA'), (54451, 'YUMBOLON ESPUMA DE POLIETILENO 15 MM'), (56896, 'MATERIAL BASE TUBERIA Ø4 SCH 40')]
    # Extraer los nombres de productos de la lista
    nombreProducto = [product[1] for product in listaPrecargada]    
    # Agregar los nombres de productos al cuadro combinado
    form.ComboBoxMaterialBase.addItems(nombreProducto) 
    numero_duplas = len(listaPrecargada)
    print("Número de duplas:", numero_duplas)
    return listaPrecargada 

# Función para manejar el evento de clic en el botón de actualización
def on_update_button_clicked():
    # Actualizar la lista de productos al inicio
    update_product_list()

def obtener_id_product():
    #Extracion del valor del campo directamente del formualrio
    if not inv: return None
    nomsis = inv.ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Part Number").Value
    barcodeProducto = nomsis       
    # Buscar el producto en Odoo por su nombre en el modelo product.template
    product_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'search', [[['barcode', '=', barcodeProducto]]])[0]
    return product_ids
  
def obtener_variable_ideMaterial():
    NombreMaterialbase = str(form.ComboBoxMaterialBase.currentText())
    return NombreMaterialbase

def obtener_id_material_base():
    NombreMaterialbase = obtener_variable_ideMaterial()
    if not models: return None    
    # Buscar el material base en Odoo por su nombre en el modelo product.product.
    # Hacemos la búsqueda más robusta para evitar el IndexError.
    search_result = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search', [[['name', '=', NombreMaterialbase]]])
    if search_result:
        return search_result[0] # Devuelve el primer ID encontrado
    else:
        return None # Devuelve None si no se encontró nada

def API_Autodesk_Inventor_imput():    
    NombreMaterialbase = obtener_variable_ideMaterial()
    # Verificar si el documento activo es un archivo de pieza (part)
    try:
        # Intentar acceder al objeto de definición de componente
        part = inv.ActiveDocument.ComponentDefinition         
        personalizada_material_base = part.Document.PropertySets.Item("User Defined Properties").Item("Material Base")
        # Establecer un nuevo valor para la propiedad "diseñador"
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
    obtener_id_product()  

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
    get_product_of_list()
    form.lblMensaje.setText("Consulta en el menu desplegable el Material Base")
    form.btnValidar.clicked.connect(on_click_validar)
    form.btnConfiMateBase.clicked.connect(create_bom_for_product)
    form.btnActualizar.clicked.connect(on_update_button_clicked)
    form.btnCerrar.clicked.connect(on_clickCerrar)