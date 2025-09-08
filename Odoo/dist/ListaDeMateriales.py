import win32com.client as wc
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.uic import loadUi
import xmlrpc.client # Libreria API Oddo
from PyQt6 import QtWidgets, uic

# --- Variables Globales que se inicializarán en run_lista_materiales ---
inv = None
app = None
formLM = None
models = None
uid = None
odoo_db = None
odoo_pass = None
# Salir de la aplicación al cerrar todos los formularios

# Conexión a Odoo
odoo_url = 'http://192.168.10.13:8069'
odoo_db = 'PruebaCFReA'
odoo_user = 'it@automate-corp.com'
odoo_pass = 'Auto1234-'

UdM = {#unidades de medida (Longitudes) validas entre Autodesk inventor y odoo
    "mm": 6,
    "cm": 8,
    "in": 17,
    "pie": 18,
    "yd": 19,
    "m": 5,
    "km": 7,
    "mi": 20
}

#region validacion si existe determinado nombre en el maestro de productos
def validacion_existe__el_material_base(Nombre : str) -> bool:
    if not models:
        return False    

    #Buscamos el producto por codigo de barras
    producto = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search',[[('name', 'ilike', Nombre)]])

    #si lo encuentra retornara Verdadero y si no lo encuentra retornara False
    return True if producto else False
#endregion

#region validacion si existe determinado codigo
def validacion_existe_el_codigo(codigo : str) -> bool:
    if not models:
        return False    

    #Buscamos el producto por codigo de barras
    producto = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search',[[('barcode', '=', codigo)]])

    #si lo encuentra retornara Verdadero y si no lo encuentra retornara False
    return True if producto else False
#endregion


#region Validacion unidades de medida de los 700
def validacion_unds_med(document : wc.CDispatch):
    if not models:
        return False
    


    #Validar que si el producto base tiene una unidad de medida en odoo de longitud 

    id_uni_med = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search_read',[[('name', 'ilike', document.Document.PropertySets.Item(4).Item("Material Base").Value)]],{'fields':['uom_id']})[0]['uom_id'][0]
    id_uni_med = models.execute_kw(odoo_db, uid, odoo_pass, 'uom.uom', 'search_read',[[('id', '=', id_uni_med)]],{'fields':['category_id']})[0]['category_id']# 4 = Longitud / Distancia, 2 = Peso


    #Si el producto base tiene una unidad de medida de longitud validar que el elemento '730' tenga un atributo length o largo

    match id_uni_med[0]:
        case 1:
            return True
        case 2: #Peso
            #Si el producto base 700 tiene como unidad de medida Peso (Mass) si el producto 730 tiene masa 'N/D' error pedir que actualice los valores
            if document.Document.PropertySets.Item(3).Item('Mass').Value == 0:
                print(f"Actualice las propiedades fisicas del producto {document.Document.PropertySets.Item(3).Item('Part Number').Value}")
                formLM.lblMensaje.setText(f"Actualice las propiedades fisicas del producto {document.Document.PropertySets.Item(3).Item('Part Number').Value}")
                return False
        case 4: #Longitud
            #Si el producto base 700 tiene como unidad de medida Longitud (Length o largo) si el producto 730 no tiene ninguno de los dos parametros o esta en 0 retornar un mensaje


            
            
            if not document.BOMQuantity.BaseUnits in UdM:
                print(f"el componente ({document.Document.PropertySets.Item(3).Item('Part Number').Value}) contiene una unidad de medida invalida ({document.BOMQuantity.BaseUnits})")
                formLM.lblMensaje.setText(f"el componente ({document.Document.PropertySets.Item(3).Item('Part Number').Value}) contiene una unidad de medida invalida ({document.BOMQuantity.BaseUnits})")
                return False

        #Esta excepcion en el caso de que el producto base (700) tenga una unidad de medida distinta a (Unidad : 1, Peso: 2, Longitud: 4)
        case other:
            print(f"El producto ({document.Document.PropertySets.Item(3).Item('Part Number').Value}) tiene como material Base ({document.Document.PropertySets.Item(4).Item('Material Base').Value}) el cual tiene una unidad de medida incorrecta ({id_uni_med[1]})")
            formLM.lblMensaje.setText(f"El producto ({document.Document.PropertySets.Item(3).Item('Part Number').Value}) tiene como material Base ({document.Document.PropertySets.Item(4).Item('Material Base').Value}) el cual tiene una unidad de medida incorrecta ({id_uni_med[1]})")
            
            return False

    return True
#endregion

#region validacion de parametros por cada componente
def validacion_parametros(component : wc.CDispatch):


    #si el producto no es de los 650 tiene que tener aspecto 
    #validar si existe la propiedad o esta vacia 

    parametros = component.Document.PropertySets


    try:

        parametro = "part number"
        if not validacion_existe_el_codigo(parametros.Item(3).Item(parametro).Value):
            print(f"El producto ({parametros.Item(3).Item(parametro).Value}) no existe en el maestro de productos")
            formLM.lblMensaje.setText(f"El producto ({parametros.Item(3).Item(parametro).Value}) no existe en el maestro de productos")
            
            return False
         
        #Validacion Aspecto     

        #Desduzco la categoria del producto en funcion de como comienza su codigo
        grupo = parametros.Item(3).Item(parametro).Value[:3]


        #hago la validacion por los tres primeros numeros del codigo y si es numerico
        
        if not grupo:  # Si el grupo está vacío
            print(f"El grupo del producto ({parametros.Item(3).Item(parametro).Value}) está vacío.")
            return False
        elif not grupo.isdigit():  # Si el grupo no es numérico
            print("El grupo no es numérico.")
            return False
        elif len(grupo) != 3:  # Si el grupo no tiene longitud 3
            print("El grupo no tiene longitud 3.")
            return False


        #si el grupo es diferente a un emsamble validar que cuente con el aspecto y el material
        if grupo != '650':
            arreglo_parametros = {"Material" : 3,"Appearance" : 3}

            for parametro, Item in arreglo_parametros.items():
                if not parametros.Item(Item).Item(parametro).Value:
                    print(f"El producto ({parametros.Item(3).Item('Part Number').Value}) no cuenta con un {parametro}")
                    formLM.lblMensaje.setText(f"El producto ({parametros.Item(3).Item('Part Number').Value}) no cuenta con un {parametro}")

        
            if grupo == '730':
                
                parametro = "Material Base"
                
                if not parametros(4)(parametro).Value:
                    #validar si el Material Base si existe
                    print(f"El producto ({parametros.Item(3).Item('Part number').Value})  no cuenta con un Material Base")
                    formLM.lblMensaje.setText(f"El producto ({parametros.Item(3).Item('Part Number').Value}) no cuenta con un {parametro}")
                    return False
                
                
                elif not validacion_existe__el_material_base(parametros.Item(4).Item(parametro).Value) :
                    print(f"El Material Base del producto ({parametros.Item(3).Item('Part number').Value}) no existe en el maestro de productos" )
                    formLM.lblMensaje.setText(f"El Material Base del producto ({parametros.Item(3).Item('Part number').Value}) no existe en el maestro de productos" )
                    return False
                
                #Si en efecto el material base existe en el maestro de productos valido las unidades de medida
                #Si el Producto 730 tiene como material base un producto que se mide en longitudes debe de tener en la unidad base una medida de longitudes tambien

                elif not validacion_unds_med(component):
                    return False

        arreglo_parametros = {'Mass' : 3,'Part Number' : 3,'description' : 3,'Title' : 1,'subject' : 1,'Clase 1' : 4,'Clase 2' : 4,'Clase 3' : 4}
        #Y "Appearance", "Material Base" bajo diferentes condiciones
        
        for parametro, Item in arreglo_parametros.items():
            if not parametros.Item(Item).Item(parametro).Value:
                print(f"El producto ({parametros.Item(3).Item('Part Number').Value}) no cuenta con un {parametro}")
                formLM.lblMensaje.setText(f"El producto ({parametros.Item(3).Item('Part Number').Value}) no cuenta con un {parametro}")
                return False

        
    #Excepcion cuando no encuentra el parametro
    except wc.pywintypes.com_error:
        print(f"el parametro: {parametro} no existe, en el producto ({parametros.Item(3).Item('Part Number').Value})")
        formLM.lblMensaje.setText(f"el parametro: {parametro} no existe, en el producto ({parametros.Item(3).Item('Part Number').Value})")
        return False

    return True
#endregion

#region Metodos Recursivos
#Metodo recursivo que imprime Producto_Padre, Producto_Hijo, Cantidad
def metodo_de_recursividad(elemento : wc.CDispatch, Padre : str , nivel : int = 0):
    for objeto in elemento:
        parte = objeto.ComponentDefinitions(1)
        atributos = parte.Document.PropertySets

        Part_Number = atributos.Item(3).Item("part number").value
        
        #Valido los datos de cada uno de los elementos
        if validacion_parametros(parte):
            print((nivel * "    ")+ Padre + " -> " + Part_Number + " -> " + str(objeto.ItemQuantity))
            formLM.lblMensaje.setText((nivel * "    ")+ Padre + " -> " + Part_Number + " -> " + str(objeto.ItemQuantity))

            #Imprimir (Masa, Longitudes o unidades) dependiendo de la unidad de medida del 700 
            if Part_Number.startswith('730'):


                id_uni_med = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search_read',[[('name', 'ilike', atributos.Item(4).Item("Material Base").Value)]],{'fields':['uom_id']})[0]['uom_id'][0]
                id_uni_med = models.execute_kw(odoo_db, uid, odoo_pass, 'uom.uom', 'search_read',[[('id', '=', id_uni_med)]],{'fields':['category_id']})[0]['category_id'][0]# 4 = Longitud / Distancia, 2 = Peso


                #Si el Material Base tiene una unidad de medida de longitud validar que el elemento '730' tenga un atributo length o largo

                Cantidad = ""

                match id_uni_med:
                    case 2: #Peso
                        Cantidad = " -> " + str(atributos.Item(3).Item("Mass").value) + " g"
                    case 4:#Longitud
                        Cantidad = " -> " + objeto.ComponentDefinitions(1).BOMQuantity.UnitQuantity     
                


                print(((nivel + 1) * "    ")+ Part_Number  + " -> " +atributos.Item(4).Item("Material Base").value + Cantidad)
                formLM.lblMensaje.setText(((nivel + 1) * "    ")+ Part_Number  + " -> " +atributos.Item(4).Item("Material Base").value + Cantidad)

            if objeto.ChildRows != None:
                metodo_de_recursividad(objeto.ChildRows, Part_Number, (nivel + 1))

        else:
            return False
        

    return True



"""
#Metodo recursivo que solo requiere el arreglo de los hijos del ensamble
def metodo_de_recursividad(elemento : wc.CDispatch):        
    for objeto in elemento:
        parte = objeto.ComponentDefinitions(1)

        if validacion_parametros(parte):
            if objeto.ChildRows != None:
                metodo_de_recursividad(objeto.ChildRows)
        else:
            return False

        return True
"""
#endregion


#Metodo que borra las lineas de lista de materiales y retorna el id de la bom (si no esta creada la lista de materiales en mrp.bom la crea)
def metodo_borrar_Lista_Matariales(cod_sizfra_Produc : str) -> str:
    if not models:
        return ""

    #Borrar lista de materiales y obtener el id de la misma
    product_tmp = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'search',[[('barcode', '=', cod_sizfra_Produc)]], {'limit': 1})[0]
    bom = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom', 'search',[[('product_tmpl_id', '=', product_tmp)]], {'limit': 1})
    
    if bom: #primer bom del producto a este le eliminaremos las lineas de bom.line y se las crearemos otra vez
        bom_line_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom.line', 'search',[[['bom_id', '=', bom[0]]]])
        #Eliminamos la lista de materiales del ensamble
        models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom.line', 'unlink',[bom_line_ids])

    
    else: #Si la lista de materiales no esta creada creala y retornar el id
        id_product_tmpl = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'search',[[('barcode', '=', cod_sizfra_Produc)]], {'limit': 1})[0]
        bom = models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom', 'create', [[{'consumption': 'flexible', 'product_tmpl_id' : id_product_tmpl, 'product_qty' : 1}]])   
    

    return bom[0]


def metodo_de_recursividad_Lineas_LdM(elemento : wc.CDispatch, bom_id : str):
    if not models:
        return
    for objeto in elemento:

        codigo_sizfra = objeto.ComponentDefinitions(1).Document.PropertySets
        product = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search',[[('barcode', '=', codigo_sizfra(3).Item('part number').value)]], {'limit': 1})[0]

        cantidad = objeto.ItemQuantity
        models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom.line', 'create', [[{'bom_id': bom_id, 'product_id' : product, 'product_qty' : cantidad}]])

        if objeto.ChildRows != None:
            
            bom = metodo_borrar_Lista_Matariales(codigo_sizfra(3).Item("part number").value)

            metodo_de_recursividad_Lineas_LdM(objeto.ChildRows, bom)

        if codigo_sizfra(3).Item("part number").value.startswith('730'):
            #Borrar lista de materiales y obtener el id de la misma

            bom = metodo_borrar_Lista_Matariales(codigo_sizfra(3).Item("part number").value)


            #validar la unidad de medida del 700 y en base a ello traer la masa o la longitud
            product = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search',[[('name', 'ilike', codigo_sizfra(4).Item("Material Base").value)]], {'limit': 1})[0]

            id_uni_med = models.execute_kw(odoo_db, uid, odoo_pass, 'product.product', 'search_read',[[('name', 'ilike', codigo_sizfra(4).Item("Material Base").value)]],{'fields':['uom_id']})[0]['uom_id'][0]
            id_uni_med = models.execute_kw(odoo_db, uid, odoo_pass, 'uom.uom', 'search_read',[[('id', '=', id_uni_med)]],{'fields':['category_id']})[0]['category_id'][0]# 4 = Longitud / Distancia, 2 = Peso

            match id_uni_med:
                case 1: #Unidades
                    cantidad = objeto.ItemQuantity
                
                case 2: #Peso
                    #Si el Material Base 700 tiene como unidad de medida Peso (Mass) si el producto 730 tiene masa 'N/D' error pedir que actualice los valores
                    cantidad = objeto.ComponentDefinitions(1).Document.PropertySets(3)("Mass").value
                    product_uom_id = 13 # 13 : Siempre en Gramos
                
                case 4: #Longitud
                    #Si el producto 700 tiene una unidad de medida de longitud
                    cantidad = objeto.ComponentDefinitions(1).BOMQuantity.UnitQuantity.split(" ")[0]

                    # Reemplazar la coma por un punto para obtener un formato numérico válido
                    cantidad = cantidad.replace(',', '.')
                    # Convertir la cadena a float
                    cantidad = float(cantidad)

                    #---- Unidad de medida ----
                    product_uom_id = UdM[objeto.ComponentDefinitions(1).BOMQuantity.BaseUnits]

            models.execute_kw(odoo_db, uid, odoo_pass, 'mrp.bom.line', 'create', [[{'bom_id': bom, 'product_id' : product, 'product_qty' : cantidad, 'product_uom_id': product_uom_id}]])


def principal():
    Ensamble = inv.ActiveDocument    
    Part_number = Ensamble.ComponentDefinitions(1).Document.PropertySets(3).Item("part number").value    
    #Validacion de datos del ensamble general
    if validacion_parametros(Ensamble.ComponentDefinitions(1)) and metodo_de_recursividad(Ensamble.ComponentDefinition.BOM.BOMViews.Item(2).BOMRows, Part_number, 0):
        bom =  metodo_borrar_Lista_Matariales(Part_number)
        Ensamble = Ensamble.ComponentDefinition.BOM.BOMViews(2).BOMRows
        metodo_de_recursividad_Lineas_LdM(Ensamble, bom)
        #arranque_codigo()
        formLM.lblMensaje.setText("Hemos cargado tu lista de materiales exitosamente")
    else:
        print("Error")
        formLM.lblMensaje.setText("Error")

def arranque_codigo():  
    global formLM
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FORM_LISTA_MATERIALES_UI = os.path.join(BASE_DIR, "FormularioListaMateriales.ui")
    formLM = loadUi(FORM_LISTA_MATERIALES_UI)
    # Mostrar formulario
    formLM.show()
    formLM.lblMensaje.setText("Subiendo tus datos al sistema de información")
 
def on_clickCerrar_LM():
    if formLM:
        formLM.close()
    if app:
        app.quit()

def run_lista_materiales(inventor_instance, q_application):
    """Función principal para lanzar este formulario."""
    global inv, app, formLM, models, uid, odoo_db, odoo_pass

    inv = inventor_instance
    app = q_application

    try:
        common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
        uid = common.authenticate(odoo_db, odoo_user, odoo_pass, {})
        models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
    except Exception as e:
        QMessageBox.critical(None, "Error de Odoo", f"No se pudo conectar a Odoo: {e}")
        return

    arranque_codigo()

    if formLM:
        formLM.lblMensaje.setText("Estamos listos para cargar tu lista de Materiales")
        formLM.btnSubirLista.clicked.connect(principal)
        formLM.btnNoSubirLista.clicked.connect(on_clickCerrar_LM)
    else:
        QMessageBox.critical(None, "Error", "No se pudo cargar el formulario de Lista de Materiales.")
