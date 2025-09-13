"""
Módulo de simulación (mock) para la API de Inventor.

Este módulo proporciona clases y objetos falsos que imitan la estructura de la API de Inventor.
Permite que el código de la aplicación se ejecute sin tener Inventor instalado,
facilitando el desarrollo y las pruebas de la lógica de la aplicación.
"""

import uuid
import random

# --- Clases de Simulación ---

class MockObject:
    """Clase base para objetos simulados con un nombre."""
    def __init__(self, name=""):
        self.Name = name

class MockProperty:
    """Simula una propiedad individual de Inventor (iProperty)."""
    def __init__(self, name, value):
        self.Name = name
        self._value = value

    @property
    def Value(self):
        return self._value

    @Value.setter
    def Value(self, new_value):
        print(f"MOCK_INFO: Propiedad '{self.Name}' actualizada a -> '{new_value}'")
        self._value = new_value

class MockPropertySet(MockObject):
    """Simula un conjunto de propiedades (PropertySet)."""
    def __init__(self, name, properties):
        super().__init__(name)
        self._properties = {p.Name.lower(): p for p in properties}

    def Item(self, name):
        # Devuelve la propiedad solicitada o una propiedad vacía si no existe.
        # Hacemos la búsqueda insensible a mayúsculas para mayor robustez.
        prop = self._properties.get(name.lower())
        if not prop:
            # Si la propiedad no existe, la creamos dinámicamente.
            # Esto simula el comportamiento de Inventor donde se puede crear una propiedad al asignarle un valor.
            print(f"MOCK_INFO: Creando propiedad personalizada '{name}' dinámicamente.")
            prop = MockProperty(name, "")
            self._properties[name.lower()] = prop
        return prop

class MockMatrix:
    """Simula una matriz de transformación de Inventor."""
    def __init__(self):
        # Simula una matriz de identidad por defecto
        self.Cell = lambda r, c: 1.0 if r == c else 0.0

class MockOccurrence(MockObject):
    """Simula un ComponentOccurrence en un ensamblaje."""
    def __init__(self, name, definition_name):
        super().__init__(name)
        self.Definition = MockComponentDefinition(definition_name)
        self.Transformation = MockMatrix()
        # Propiedad para simular la visibilidad
        self._visible = True

    @property
    def Visible(self):
        return self._visible

    @Visible.setter
    def Visible(self, value):
        self._visible = bool(value)

class MockBOMQuantity:
    """Simula la cantidad en una lista de materiales (BOM)."""
    def __init__(self):
        self.UnitQuantity = "1.000 un" # 'un' para unidades


class MockComponentDefinition(MockObject):
    """Simula una ComponentDefinition."""
    def __init__(self, name):
        super().__init__(name)
        self.BOMQuantity = MockBOMQuantity()
        # Añadimos una referencia al documento padre para acceder a las propiedades
        self.Document = None
        # Añadimos una referencia a la aplicación
        self.Application = None

class MockAssemblyComponentDefinition(MockObject):
    """Simula un AssemblyComponentDefinition que contiene ocurrencias."""
    def __init__(self, name="AssemblyDef", parent_document=None):
        super().__init__(name)
        self.Document = parent_document # Añadimos la referencia al documento padre
        # Lista de ocurrencias de componentes simuladas
        self.Occurrences = [
            MockOccurrence("Componente:1", "PiezaA"),
            MockOccurrence("Componente:2", "PiezaB"),
            MockOccurrence("SubEnsamblaje:1", "SubEnsamblajeDef"),
            MockOccurrence("Tornillo:1", "Tornillo_ISO4017"),
            MockOccurrence("Tornillo:2", "Tornillo_ISO4017"),
        ]
        self.BOMQuantity = MockBOMQuantity()

# --- Generador de Documentos Simulados ---
_document_counter = 0

def create_new_mock_document(group_id=None):
    """
    Fábrica para crear nuevos documentos simulados con datos únicos.
    Esto nos permite simular la creación de múltiples piezas diferentes.
    """
    global _document_counter
    _document_counter += 1

    doc_name = f"PiezaSimulada-{_document_counter}.ipt"
    part_number = "" # Se deja vacío para que la app lo genere
    title = f"Mi Pieza de Prueba {_document_counter}"
    
    print(f"\n--- MOCK: Creando nuevo documento simulado: {doc_name} ---")

    # --- INICIO DE LA SIMULACIÓN DE PROPIEDADES ---
    design_tracking_props = MockPropertySet("Design Tracking Properties", [
        MockProperty("Part Number", part_number),
        MockProperty("Description", f"Descripción para la pieza de prueba {_document_counter}"),
        MockProperty("Material", "Acero (simulado)"),
        MockProperty("Mass", round(random.uniform(500, 2000), 2)), # Masa en gramos
        MockProperty("Volume", round(random.uniform(100, 300), 2)), # Volumen en cm^3
        MockProperty("Appearance", "Acero Pulido (simulado)"),
        MockProperty("Designer", ""), # Se llenará desde la app
        MockProperty("Stock Number", ""), # Se llenará desde la app
    ])
    summary_info_props = MockPropertySet("Inventor Summary Information", [
        MockProperty("Title", title),
        MockProperty("Subject", "Ubicación Simulada"),
        MockProperty("Keywords", "simulacion, prueba, odoo"),
        MockProperty("Author", ""), # Se llenará desde la app
    ])
    doc_summary_props = MockPropertySet("Inventor Document Summary Information", [
        MockProperty("Category", ""), # Se llenará desde la app
    ])
    
    user_props_list = [
        MockProperty("Clase 1", ""),
        MockProperty("Clase 2", ""),
        MockProperty("Clase 3", ""),
        MockProperty("Material Base", ""), # Para productos 730
    ]

    # --- MEJORA PARA PRUEBAS ---
    # Si el grupo es 730, añadimos la iProperty simulada "Codigo Sizfra".
    if group_id == "730":
        print("MOCK_INFO: Añadiendo iProperty 'Codigo Sizfra' para prueba de Material Base.")
        user_props_list.append(MockProperty("Codigo Sizfra", "7004030000003"))

    user_defined_props = MockPropertySet("User Defined Properties", user_props_list)
    
    # Creamos un objeto que se comporta como la colección PropertySets
    class MockPropertySets:
        def __init__(self):
            self._sets = {
                "Design Tracking Properties": design_tracking_props,
                "Inventor Summary Information": summary_info_props,
                "Inventor Document Summary Information": doc_summary_props,
                "User Defined Properties": user_defined_props,
            }
        def Item(self, key):
            return self._sets.get(key)

    return MockDocument(doc_name, MockPropertySets())
    # --- FIN DE LA SIMULACIÓN DE PROPIEDADES ---

class MockDocument(MockObject):
    """Simula un Documento de Inventor (ej. un ensamblaje)."""
    def __init__(self, name, property_sets_instance):
        super().__init__(name)
        self.FullFileName = f"C:\\Simulated\\Path\\{name}"
        self.PropertySets = property_sets_instance
        # La definición del componente ahora se refiere a sí misma para acceder a las propiedades
        self.ComponentDefinition = MockComponentDefinition(name)
        self.ComponentDefinition.Document = self

    def Save(self):
        print(f"MOCK_INFO: Documento '{self.Name}' guardado.")

class MockApplication:
    """Simula el objeto principal de la aplicación de Inventor."""
    def __init__(self):
        # Inicia con un documento por defecto
        self.ActiveDocument = create_new_mock_document()

    def CreateNewDocument(self, group_id=None):
        """Simula la creación de un nuevo documento y lo establece como activo."""
        self.ActiveDocument = create_new_mock_document(group_id)
        return self.ActiveDocument

# --- Instancia Global Simulada ---

# Esta instancia será importada por otros módulos cuando se ejecute sin Inventor.
app_instance = MockApplication()

def get_inventor_app():
    """
    Devuelve la instancia simulada de la aplicación de Inventor.
    Esta función imita el comportamiento de obtener la aplicación real.
    """
    print("ADVERTENCIA: Usando la instancia simulada de Inventor (inventor_mock).")
    return app_instance