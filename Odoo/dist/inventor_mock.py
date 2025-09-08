"""
Módulo de simulación (mock) para la API de Inventor.

Este módulo proporciona clases y objetos falsos que imitan la estructura de la API
de Inventor. Permite que el código de la aplicación se ejecute sin tener
Inventor instalado, facilitando el desarrollo y las pruebas de la lógica
de la aplicación que no depende directamente del entorno de Inventor.
"""

import uuid

# --- Clases de Simulación ---

class MockObject:
    """Clase base para objetos simulados con un nombre."""
    def __init__(self, name=""):
        self.Name = name

class MockProperty:
    """Simula una propiedad individual de Inventor (iProperty)."""
    def __init__(self, name, value):
        self.Name = name
        self.Value = value

class MockPropertySet(MockObject):
    """Simula un conjunto de propiedades (PropertySet)."""
    def __init__(self, name, properties):
        super().__init__(name)
        self._properties = {p.Name: p for p in properties}

    def Item(self, name):
        # Devuelve la propiedad solicitada o una propiedad vacía si no existe.
        return self._properties.get(name, MockProperty(name, ""))

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
        self.UnitQuantity = "1.000 un"


class MockComponentDefinition(MockObject):
    """Simula una ComponentDefinition."""
    def __init__(self, name):
        super().__init__(name)
        self.BOMQuantity = MockBOMQuantity()

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

class MockDocument(MockObject):
    """Simula un Documento de Inventor (ej. un ensamblaje)."""
    def __init__(self, name="Assembly.iam"):
        super().__init__(name)
        self.FullFileName = f"C:\\Simulated\\Path\\{name}"
        self.ComponentDefinition = MockAssemblyComponentDefinition(parent_document=self)

        # --- INICIO DE LA SIMULACIÓN DE PROPIEDADES ---
        # Creamos conjuntos de propiedades simulados con datos de ejemplo.
        design_tracking_props = MockPropertySet("Design Tracking Properties", [
            MockProperty("Part Number", "650-SIMULADO-001"),
            MockProperty("Description", "Componente simulado para pruebas"),
            MockProperty("Material", "Acero (simulado)"),
            MockProperty("Mass", 1250.0), # Masa en gramos
            MockProperty("Volume", 159.0), # Volumen en cm^3
            MockProperty("Appearance", "Acero Pulido")
        ])
        summary_info_props = MockPropertySet("Inventor Summary Information", [
            MockProperty("Title", "Mi Ensamblaje Simulado"),
            MockProperty("Subject", "Ubicación Simulada"),
            MockProperty("Keywords", "simulacion, prueba, odoo")
        ])
        doc_summary_props = MockPropertySet("Inventor Document Summary Information", [
            MockProperty("Category", "PRE-ENSAMBLES"),
        ])
        
        # Creamos un objeto que se comporta como la colección PropertySets
        class MockPropertySets:
            def __init__(self):
                self._sets = {
                    "Design Tracking Properties": design_tracking_props,
                    "Inventor Summary Information": summary_info_props,
                    "Inventor Document Summary Information": doc_summary_props,
                }
            def Item(self, key):
                return self._sets.get(key)

        self.PropertySets = MockPropertySets()
        # --- FIN DE LA SIMULACIÓN DE PROPIEDADES ---

class MockApplication:
    """Simula el objeto principal de la aplicación de Inventor."""
    def __init__(self):
        self.ActiveDocument = MockDocument()

# --- Instancia Global Simulada ---

# Esta instancia será importada por otros módulos cuando se ejecute sin Inventor.
app = MockApplication()

def get_inventor_app():
    """
    Devuelve la instancia simulada de la aplicación de Inventor.
    Esta función imita el comportamiento de obtener la aplicación real.
    """
    print("ADVERTENCIA: Usando la instancia simulada de Inventor (inventor_mock).")
    return app