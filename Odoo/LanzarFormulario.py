import random
import win32com.client as win32  # Libreria API Autodesk
import xmlrpc.client  # Libreria API Odoo
import base64
import sys
from PyQt6 import QtWidgets, uic
import socket
from PyQt6.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget, QPushButton
from PyQt6.uic import loadUi

def check_internet_connection():
    try:
        # Intenta crear un socket para conectarse a un host en Internet (por ejemplo, google.com)
        socket.create_connection(("www.google.com", 80))
        form_odoo.lblMensaje_4.setText("Conexión a Internet disponible.")
        return True
    except OSError:
        # Si ocurre un error al intentar conectar, devuelve False
        form_odoo.lblMensaje_4.setText("No hay conexión a Internet, intente de nuevamente mas tarde.")
        return False

def validar_docActivo_inventor():   
    try:
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
            image_path = 'O:/5.OPERACIONES/AT/Odoo/dist/LibImaOddo/Imagen.png'
            Objeto_Aplicacion_Inevntor = Objeto_Aplicacion_Inevntor.ActiveDocument
            Objeto_Aplicacion_Inevntor.SaveAs(image_path,True)
            return encode_image_to_base64(image_path) 
        imagen()        
        return True
    except Exception as e:
        app = QtWidgets.QApplication(sys.argv)
        form_grupo = uic.loadUi("FormularioGrupo.ui")
        # Cargar el formulario principal
        form_odoo = uic.loadUi("FormularioOdoo.ui")
        form_odoo.show()
        form_grupo.show()
        QtWidgets.QMessageBox.critical(None, "Error", "No se pudo encontrar una instancia activa de Autodesk Inventor.")    
        form_grupo.close() # Cerrar el formulario si no se encuentra un documento activo en Autodesk Inventor
        form_odoo.close() # Cerrar el formulario si no se encuentra un documento activo en Autodesk Inventor
        app.close()     
        return False
    
def valida_cate_grupo():
    GrSiFor = form_grupo.ComboBoxGrupo.currentText()    
    if GrSiFor == "MATERIA PRIMA ENSAMBLE":       
        #categ = "MATERIA PRIMA ENSAMBLE"
        categ = form_odoo.txtCategoria.setText("MATERIA PRIMA ENSAMBLE")
    elif GrSiFor == "PRE-ENSAMBLES":        
        #categ = "PRE-ENSAMBLES"
        categ = form_odoo.txtCategoria.setText("PRE-ENSAMBLES")         
    elif GrSiFor == "MATERIA PRIMA PROCESADA":
        #categ = "MATERIA PRIMA PROCESADA"  
        categ = form_odoo.txtCategoria.setText("MATERIA PRIMA PROCESADA")
        return categ
                  
def generar_codigo_unico(form_grupo):
    GrSiFor = form_grupo.ComboBoxGrupo.currentText()
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
        
    rand = random.randrange(1, 9999999999)  # Genera número aleatorio en el rango indicado
    numero_aleatorio_formateado = "{:010d}".format(rand)  # Formatear el número como una cadena con 10 dígitos, añadiendo ceros a la izquierda si es necesario    
    codigonuevo = grupoNum + numero_aleatorio_formateado  # Concatenación de la variable del grupo con el aleatorio de 10 dígitos para que quede de 13 dígitos    
    return codigonuevo

# Conectarse a odoo hacer una validación y escribir en odoo si el codigo no esta repetido
def API_Odoo(codigonuevo):
    codigonuevo = form_odoo.txtCodigo.text()    
    Material = str(form_odoo.txtMaterial.text())
    Masa = str(form_odoo.txtMasa.text())
    volume = str(form_odoo.txtVolume.text())
    GrSiFor = form_grupo.ComboBoxGrupo.currentText()
    nombre = form_odoo.txtNombreSis.text()
    clases = actualizar_labels_desde_combobox()
    acabado = form_odoo.txtAcabado.text()
    descripcion = form_odoo.txtDescripcion.text()
    subject = form_odoo.txtAlmacena.text()    
    email = form_odoo.ComboBoxEmail.currentText()
    palabclave = form_odoo.textPalabraClave.toPlainText()
    path = win32.Dispatch("Inventor.Application").ActiveDocument.FullFileName
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
        image_path = 'O:/5.OPERACIONES/AT/Odoo/dist/LibImaOddo/Imagen.png'
        Objeto_Aplicacion_Inevntor = Objeto_Aplicacion_Inevntor.ActiveDocument
        Objeto_Aplicacion_Inevntor.SaveAs(image_path,True)
        return encode_image_to_base64(image_path) 
    imagen()
    
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
    
    usuario = form_odoo.ComboBoxEmail.currentText()
    clave = form_odoo.txtClave.text() 
    odoo_url = 'http://192.168.10.13:8069'
    odoo_db = 'PruebaCFReA'
    odoo_user = usuario
    odoo_pass = clave

    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
    uid = common.authenticate(odoo_db, odoo_user, odoo_pass, {})

    
    if uid:  # Verificar que la autenticación sea exitosa
        models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

        new_product_data = {
            'name': nombre,
            'barcode': codigonuevo,
            'image_1920': imagen(),
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
            #'route_ids' : [1, route],
            'weight' : Masa,
            'volume' : volume,
            'x_material' : Material,
            'x_Tipo_Inventario': tipoInven,
            'x_subpartida': 9714,             
            'description_pickingout': codigonuevo,
            'x_categoria_3': clases,
            'x_acabado': acabado,
            #'x_email_autor': email,
            'x_descripcion': descripcion, 
            'x_subject': subject,           
            'x_palabras_claves': palabclave,   
            'x_docPath': path,              
            'responsible_id' : 2
        }

        try:
            new_product_id = models.execute_kw(odoo_db, uid, odoo_pass,'product.template', 'create', [new_product_data])                                                
            print("Nuevo producto creado en el ERP Odoo con ID:", new_product_id)
            form_odoo.lblMens1.setText(f"Nuevo producto creado en el ERP Odoo con ID: {new_product_id}")
                        
        except xmlrpc.client.Fault as error:
            if 'Códigos de barras ya asignados' in error.faultString:
                start_index = error.faultString.find('"') + 1
                end_index = error.faultString.find('"', start_index)
                codigo_repetido = error.faultString[start_index:end_index]
                print("Código de producto repetido:", codigo_repetido)
                form_odoo.lblMens1.setText("Código de producto repetido:", codigo_repetido)
                #messagebox.showinfo("CODIGO REPETIDO FIN DEL PROGRAMA")
                # Por ejemplo, puedes imprimir un mensaje y salir del programa
                print("El código de barras está repetido. Saliendo del programa.")
                form_odoo.lblMensaje.setText("El código de barras está repetido. Saliendo del programa.")
                return True
            else:
                print("Error:", error)
    else:
        print("Error de autenticación en Odoo. Verifica las credenciales y la URL.")
        form_odoo.lblMensaje.setText("Error de autenticación en Odoo. Verifica las credenciales y la URL.")
def API_Autodesk_Inventor_imput(codigonuevo):    
    codigonuevo = form_odoo.txtCodigo.text()     
    cate = form_odoo.txtCategoria.text()
    cat1 = form_odoo.txtCat1.text()
    cat2 = form_odoo.txtCat2.text()
    cat3 = form_odoo.txtCat3.text() 
    designer = form_odoo.lblMensaje_6.text() 
    autor = form_odoo.ComboBoxEmail.currentText()
    palabclave = form_odoo.textPalabraClave.toPlainText()
    product_ids = obtener_id_product()
    new_product_id = product_ids   
    # Verificar si el documento activo es un archivo de pieza (part)
    try:
        # Intentar acceder al objeto de definición de componente
        part = invDoc.ComponentDefinition
        # Acceder a la propiedad "Part Number" de la parte
        part_number_property = part.Document.PropertySets.Item("Design Tracking Properties").Item("Part Number")
        # Establecer un nuevo valor para la propiedad "Part Number"
        new_part_number = codigonuevo
        part_number_property.Value = new_part_number
        print("Se ha establecido el nuevo número de pieza en Autodesk Inventor:", new_part_number)
        form_odoo.lblMensaje.setText(f"Se ha establecido el nuevo número de pieza en Autodesk Inventor: {new_part_number}")
        # # Acceder a la propiedad "Description" de la parte
        categoria_property = part.Document.PropertySets.Item("Inventor Document Summary Information").Item("Category")
        # Establecer un nuevo valor para la propiedad "categoria"
        new_categoria = cate.lower()
        categoria_property.Value = new_categoria
        print("Se ha establecido la nueva categoria de la pieza en Autodesk Inventor:", new_categoria)  
        form_odoo.lblMensaje_4.setText(f"Se ha establecido la nueva categoria de la pieza en Autodesk Inventor: {new_categoria}")
        categoria_designer = part.Document.PropertySets.Item("Design Tracking Properties").Item("Designer")
        # Establecer un nuevo valor para la propiedad "diseñador"
        new_designer = designer
        categoria_designer.Value = new_designer 
        print("Se ha establecido el diseñador de la pieza en Autodesk Inventor:", new_designer)  
        categoria_stock_number = part.Document.PropertySets.Item("Design Tracking Properties").Item("Stock Number")
        # Establecer un nuevo valor para la propiedad "diseñador"
        new_stock_number = new_product_id 
        categoria_stock_number.Value = new_stock_number 
        print("Se ha establecido el diseñador de la pieza en Autodesk Inventor:", new_stock_number)    
        # Establecer un nuevo valor para la propiedad "autor"
        categoria_autor = part.Document.PropertySets.Item("Inventor Summary Information").Item("Author")
        new_autor = autor
        categoria_autor.Value = new_autor 
        print("Se ha establecido el autor de la pieza en Autodesk Inventor:", new_autor)  
        categoria_PalabraClave = part.Document.PropertySets.Item("Inventor Summary Information").Item("Keywords")
        new_PalabraClave = palabclave
        categoria_PalabraClave.Value = new_PalabraClave 
        print("Se ha establecido las palabras claves de la pieza en Autodesk Inventor:", new_PalabraClave)
        form_odoo.lblMensaje_5.setText(f"Se ha establecido las palabras claves de la pieza en Autodesk Inventor: {new_PalabraClave}")   
               # Propiedades personalizadas adicionales
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
            except Exception as e:
                print(f"Error al establecer la propiedad en Autodesk Inventor '{property_name}':", e)

        # Guardar el documento con las nuevas propiedades
        invDoc.Save()
    except Exception as e:
        print("Error: ", e)
        print("El documento activo no es un archivo de pieza (part).")    


def validar_barcode():#, imagen(image_path)):
    try:           
        valbarcode = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Part Number").value
        mate = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Material").value
        descripcion = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Description").value
        almacena = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Subject").value        
        acab = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Appearance").value
        masa = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Mass").value        
        cat1 = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("User Defined Properties").Item("Clase 1").value
        cat2 = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("User Defined Properties").Item("Clase 2").value
        cat3 = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("User Defined Properties").Item("Clase 3").value
        nomsis = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Title").value
        volume = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Volume").value
        cate = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Document Summary Information").Item("Category").value
        palabclave = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Keywords").value

        #ImagForm = imagen(image_path)        
        if valbarcode == "":                
            form_odoo.lblMensaje.setText("Autodesk Inventor esta listo para recibir su carga.")
            #QtWidgets.QMessageBox.critical("Autodesk Inventor esta listo para recibir su carga.")
            return False
        else:                         
            form_odoo.txtCodigo.setText(valbarcode)
            form_odoo.txtCodigo.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura                     
            form_odoo.txtNombreSis.setText(nomsis)
            form_odoo.txtNombreSis.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtCat1.setText(cat1)
            form_odoo.txtCat1.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtCat2.setText(cat2)
            form_odoo.txtCat2.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtCat3.setText(cat3)
            form_odoo.txtCat3.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtMaterial.setText(mate)
            form_odoo.txtMaterial.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtAcabado.setText(acab)
            form_odoo.txtAcabado.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtMasa.setText(str(round(masa/1000,2)))
            form_odoo.txtMasa.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.lblMensaje.setText("Datos obtenidos de Autodesk Inventor.")
            form_grupo.close()
            form_odoo.btnEnviar.setEnabled(False)  # Deshabilitar el botón si no hay texto
            form_odoo.btnEnviar.setStyleSheet("background-color: gray; color: white")
            form_odoo.txtDescripcion.setText(descripcion)
            form_odoo.txtDescripcion.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtAlmacena.setText(almacena)
            form_odoo.txtAlmacena.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura            
            form_odoo.txtCategoria.setText(cate)
            form_odoo.txtCategoria.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.txtVolume.setText(str(round(volume/1,2)))
            form_odoo.txtVolume.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
            form_odoo.textPalabraClave.setText(palabclave)
            form_odoo.textPalabraClave.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura

            return True
    except Exception as e:
        form_odoo.lblMensaje.setText("Error de comunicación con Autodesk Inventor")
        QtWidgets.QMessageBox.critical(None, "Error", "Error de comunicación con Autodesk Inventor")
        return False

def abrir_formulario_principal():
    # Actualizar el código antes de mostrar el formulario principal       
    codigo = generar_codigo_unico(form_grupo) 
    valida_cate_grupo()      
    form_odoo.txtCodigo.setText(codigo) 
    form_odoo.txtCodigo.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura     
    form_odoo.lblMens1.setText("Aplicativo listo para conectar con Autodesk Inventor, ERP Odoo, Sistema información Sizfra, ")
    form_odoo.show()
    form_grupo.close()
    return(codigo)

def abrir_formulario_grupo():
    # Mostrar el formulario previo
    form_grupo.show()

def on_clickCerrar():
    app.quit()     
    
def on_click_validar():     
    mate = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Material").value
    descripcion = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Description").value
    almacena = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Subject").value
    acab = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Appearance").value
    masa = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Mass").value
    volume = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Design Tracking Properties").Item("Volume").value
    nombre = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Title").value
    palabclave = win32.GetActiveObject("Inventor.Application").ActiveDocument.ComponentDefinition.Document.PropertySets.Item("Inventor Summary Information").Item("Keywords").value

    usuario = form_odoo.ComboBoxEmail.currentText()    
    if usuario == "admin@automate-corp.com":
        userlbl = "Administrador"  
    elif usuario == "it@automate-corp.com":
        userlbl = "Christiam Fernando Rey Anaya"          
    elif usuario == "ingenieria1@automate-corp.com":
        userlbl = "Jesus Alberto Ariza Gil"    
    elif usuario == "ingenieria2@automate-corp.com":
        userlbl = "Sara Zambrano Naranjo"
    elif usuario == "ingenieria3@automate-corp.com":
        userlbl = "Carlos Alberto Chavarria Jaramillo"
    elif usuario == "ingenieria4@automate-corp.com":
        userlbl = "Juan Carlos Atehortúa Montes" 
    elif usuario == "ingenieria5@automate-corp.com":
        userlbl = "Andres Felipe Marin Quintero" 
    elif usuario == "ingenieria6@automate-corp.com":
        userlbl = "Daniel Londoño Serna" 
    elif usuario == "electrica@automate-corp.com":
        userlbl = "Monica Yepes Medina" 
    elif usuario == "produccion@automate-corp.com":
        userlbl = "Johan Sebastian Gaviria Ruiz"  
    elif usuario == "sistemas@automate-corp.com":
        userlbl = "Juan Andres Pernet"   
    elif usuario == "operaciones@automate-corp.com":
        userlbl = "Juan Alejandro Diaz"                
    else:
        form_odoo.lblMens1.setText("Selecciona el usuario") 
                     
    if nombre == "":        
               
        form_odoo.lblMensaje_5.setText("Autodesk Inventor esta listo para recibir su carga.")

        return False
    else:
        generar_codigo_unico(form_grupo)
        form_odoo.txtCodigo.text()
        form_odoo.txtCodigo.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.txtDescripcion.setText(descripcion)
        form_odoo.txtDescripcion.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura  
        form_odoo.txtAlmacena.setText(almacena)
        form_odoo.txtAlmacena.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura          
        form_odoo.txtNombreSis.setText(nombre)
        form_odoo.txtNombreSis.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.txtMaterial.setText(mate)
        form_odoo.txtMaterial.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.txtAcabado.setText(acab)
        form_odoo.txtAcabado.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.txtMasa.setText(str(round(masa/1000,2)))
        form_odoo.txtMasa.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.lblMensaje.setText("Datos obtenidos del aplicativo Autodesk Inventor Professional.")
        form_odoo.lblMensaje_6.setText(userlbl)
        form_odoo.lblMens1.setText("Bienvenido,"+ userlbl)
        form_odoo.btnValidar.setStyleSheet("background-color: blue; color: white;")
        form_odoo.txtVolume.setText(str(round(volume/1,2)))
        form_odoo.txtVolume.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura        
        form_odoo.txtCategoria.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.txtDescripcion.setText(descripcion)
        form_odoo.txtDescripcion.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.txtAlmacena.setText(almacena)
        form_odoo.txtAlmacena.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.textPalabraClave.setText(palabclave)
        form_odoo.textPalabraClave.setReadOnly(True)  # Establecer el cuadro de texto como solo lectura
        form_odoo.lblMensaje_5.setText("Codigo creado con exito")#, generar_codigo_unico(form_grupo))  
                 
def obtener_id_product():
    #Extracion del valor del campo directamente del formualrio
    barcodeProducto = str(form_odoo.txtCodigo.text())       
    # Buscar el producto en Odoo por su nombre en el modelo product.template
    product_ids = models.execute_kw(odoo_db, uid, odoo_pass, 'product.template', 'search', [[['barcode', '=', barcodeProducto]]])[0]
    return product_ids

def on_click(codigonuevo):
    descripcionfor = form_odoo.ComboBoxDescripcion.currentText()           
    API_Odoo(codigonuevo)
    obtener_id_product()
    API_Autodesk_Inventor_imput(codigonuevo)    
    form_odoo.lblMensaje_5.setText("Producto cargado correctamente en Autodesk Inventor, ERP Odoo, BD Sizfra")    
    GrSiFor = form_grupo.ComboBoxGrupo.currentText()
    if GrSiFor == "MATERIA PRIMA ENSAMBLE":        
        form_grupo.lblMens1.setText("Codigo generado con exito.")
    elif GrSiFor == "PRE-ENSAMBLES":
        import ListaDeMateriales as ldm        
        ldm               
        #form_grupo.lblMens1.setText("Codigo generado con exito.")    
    elif GrSiFor == "MATERIA PRIMA PROCESADA":
        import LanzarMaterialBase1 as lmb
        lmb  
        #form_odoo.lblMensaje5.setText("Codigo generado con exito.")    
    else:
        form_grupo.lblMens1.setText("Selecciona el grupo")

# Crear una instancia de Autodesk Inventor
inv = win32.GetActiveObject("Inventor.Application")
# Crear una instancia de Autodesk Inventor
invApp = win32.Dispatch("Inventor.Application")
# Acceder al documento activo 
invDoc = invApp.ActiveDocument
# Crear una instancia de Autodesk Inventor
validar_docActivo_inventor()
# Crear una instancia de QApplication
app = QtWidgets.QApplication(sys.argv)
# Cargar el formulario previo
form_grupo = uic.loadUi("FormularioGrupo.ui")
# Cargar el formulario principal
form_odoo = uic.loadUi("FormularioOdoo.ui")
# Limpiar combobox
form_odoo.ComboBoxDescripcion.clear()
form = loadUi("FormularioMaterialBase.ui")
formLM = loadUi("FormularioListaMateriales.ui")
form_odoo.lblMensaje_5.setText("Autodesk Inventor tiene un documento activo.")
  
# Llamar a la función para validar el documento activo en Autodesk Inventor al abrir el formulario
if check_internet_connection():
    abrir_formulario_principal() # Si hay un documento activo, validar el campo 'Parte Numero'  
    abrir_formulario_grupo()
    validar_barcode()  
    generar_codigo_unico(form_odoo)
    # Conexión a Odoo
    odoo_url = 'http://192.168.10.13:8069'
    odoo_db = 'PruebaCFReA'
    odoo_user = 'it@automate-corp.com'
    odoo_pass = 'Auto1234-'
    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
    uid = common.authenticate(odoo_db, odoo_user, odoo_pass, {})
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')  
    
    def obtener_descripciones_categorias_3():    
        # Obtener las descripciones y IDs de categoría 3
        categorias_3 = models.execute_kw(odoo_db, uid, odoo_pass, 'x_categoria_3', 'search_read', [],
                                      {'fields': ['id', 'x_name', 'x_descripcion']})        
        return categorias_3

    def actualizar_labels_desde_combobox():
        # Obtener el índice seleccionado en el ComboBox
        indice_seleccionado = form_odoo.ComboBoxDescripcion.currentIndex()      
        # Verificar si categorias_3 es None o está vacío
        if categorias_3 is not None and len(categorias_3) > 0:
            # Obtener la información de la categoría seleccionada
            categoria_seleccionada = categorias_3[indice_seleccionado]
            cate2 = categoria_seleccionada['id']
            cate3 = categoria_seleccionada['x_descripcion']
            form_odoo.txtCat3.setText(str(cate3))  # Mostrar la descripción de la categoría 3
            cate_info = metodo_categorias(cate2)
            # Actualizar los labels txtCat2 y txtCat1 con los valores obtenidos de metodo_categorias
            form_odoo.txtCat2.setText(str(cate_info['categoria_2'][1]))
            form_odoo.txtCat1.setText(str(cate_info['categoria_1'][1]))
            return cate2

    def metodo_categorias(cate2):
        variable = models.execute_kw(odoo_db, uid, odoo_pass, 'x_categoria_3','read',[[cate2]],{'fields':['x_name','x_categoria_2']})  
        cate2_info = [variable[0]['id'],variable[0]['x_name']]
        id_categoria_2 = variable[0]['x_categoria_2']
        variable = models.execute_kw(odoo_db, uid, odoo_pass, 'x_categoria_2','read',[[id_categoria_2[0]]],{'fields':['x_categoria_1']})
        id_categoria_1 = variable[0]['x_categoria_1']  
        return {'categoria_1': id_categoria_1 ,'categoria_2': id_categoria_2,'categoria_3':  cate2_info}

    def correr_progrma_clases():
        # Llenar el ComboBox con las descripciones de categoría 3
        form_odoo.ComboBoxDescripcion.clear()
        #categorias_3 = obtener_descripciones_categorias_3()
        if categorias_3 is not None and len(categorias_3) > 0:
            for categoria in categorias_3:
                descripcion = categoria['x_name']
                form_odoo.ComboBoxDescripcion.addItem(descripcion)
                
            # Conectar la señal currentIndexChanged del ComboBox a la función actualizar_labels_desde_combobox
            form_odoo.ComboBoxDescripcion.currentIndexChanged.connect(actualizar_labels_desde_combobox)
    categorias_3 = obtener_descripciones_categorias_3()
    correr_progrma_clases()
    on_clickCerrar()
else:
    form_odoo.show()
    form_grupo.show()
    QtWidgets.QMessageBox.critical(None, "Error", "No hay conexión a Internet, intente de nuevamente mas tarde.")    
    form_grupo.close() # Cerrar el formulario si no se encuentra un documento activo en Autodesk Inventor
    form_odoo.close() # Cerrar el formulario si no se encuentra un documento activo en Autodesk Inventor
    app.close()         

def abrir_formulario_650():
    # Mostrar el formulario previo
    import ListaDeMateriales as ldm        
    ldm 
    on_clickCerrar()

def abrir_formulario_730():
    # Mostrar el formulario previo
    import LanzarMaterialBase1 as lmb
    lmb 
    on_clickCerrar()  
    
form_odoo.btn650.clicked.connect(abrir_formulario_650)
form_odoo.btn730.clicked.connect(abrir_formulario_730)
form_odoo.btnCerrarPrin.clicked.connect(on_clickCerrar)
form_grupo.btnConfirmar.clicked.connect(abrir_formulario_principal)
form_odoo.btnEnviar.clicked.connect(on_click)
form_odoo.btnValidar.clicked.connect(on_click_validar)
form_odoo.btnGenerarCod.clicked.connect(abrir_formulario_grupo)
form_odoo.show()
# Salir de la aplicación al cerrar todos los formularios
sys.exit(app.exec())




 
    