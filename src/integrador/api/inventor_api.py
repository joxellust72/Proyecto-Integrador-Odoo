"""
Módulo de la API para interactuar con Autodesk Inventor.

Esta clase encapsula la lógica para leer y escribir iProperties,
guardar documentos, capturar vistas previas y extraer datos de la
Lista de Materiales (BoM) del documento activo en Inventor.
"""
import os

class InventorApi:
    """Una clase de envoltura para interactuar con la API de Autodesk Inventor."""

    def __init__(self, app_instance, q_app_instance=None):
        """
        Inicializa la API con la instancia de la aplicación de Inventor.

        Args:
            app_instance: La instancia de la aplicación de Inventor (real o simulada).
            q_app_instance: La instancia de QApplication para procesar eventos de la UI.
        """
        self.app = app_instance
        self.q_app = q_app_instance
        self.doc = self.app.ActiveDocument if self.app else None

    def _get_property(self, prop_set_name, prop_name, default=""):
        """
        Método auxiliar privado para obtener una iProperty de forma segura.
        """
        if not self.doc:
            return default
        try:
            prop_sets = self.doc.PropertySets
            prop_set = prop_sets.Item(prop_set_name)
            return prop_set.Item(prop_name).Value
        except Exception as e:
            # No imprimimos error aquí para no llenar la consola con propiedades que no existen.
            return default

    def get_all_properties(self):
        """
        Recopila un conjunto de iProperties comunes del documento activo.

        Returns:
            dict: Un diccionario con las propiedades más relevantes del documento.
                  Los valores serán None si una propiedad no se encuentra.
        """
        if not self.doc:
            return {}
            
        return {
            "material": self._get_property("Design Tracking Properties", "Material"),
            "description": self._get_property("Design Tracking Properties", "Description"),
            "appearance": self._get_property("Design Tracking Properties", "Appearance"),
            "mass": self._get_property("Design Tracking Properties", "Mass", default=0.0),
            "volume": self._get_property("Design Tracking Properties", "Volume", default=0.0),
            "part_number": self._get_property("Design Tracking Properties", "Part Number"),
            "stock_number": self._get_property("Design Tracking Properties", "Stock Number"),
            "designer": self._get_property("Design Tracking Properties", "Designer"),
            "title": self._get_property("Inventor Summary Information", "Title"),
            "subject": self._get_property("Inventor Summary Information", "Subject"),
            "author": self._get_property("Inventor Summary Information", "Author"),
            "keywords": self._get_property("Inventor Summary Information", "Keywords"),
            "category": self._get_property("Inventor Document Summary Information", "Category"),
            "clase_1": self._get_property("User Defined Properties", "CLASE 1"),
            "clase_2": self._get_property("User Defined Properties", "CLASE 2"),
            "clase_3": self._get_property("User Defined Properties", "CLASE 3"),
        }

    def update_document_properties(self, properties_to_update):
        """
        Actualiza un conjunto de iProperties en el documento activo.

        Args:
            properties_to_update (dict): Un diccionario donde las claves son los nombres
                                         de las propiedades de iProperties (en un formato
                                         simplificado como 'part_number', 'category') y
                                         los valores son los nuevos valores a establecer.
        
        Returns:
            bool: True si todas las propiedades se actualizaron, False si hubo un error.
        """
        if not self.doc:
            print("ERROR: No hay documento activo para actualizar propiedades.")
            return False
        
        prop_map = {
            "part_number": ("Design Tracking Properties", "Part Number"),
            "stock_number": ("Design Tracking Properties", "Stock Number"),
            "designer": ("Design Tracking Properties", "Designer"),
            "author": ("Inventor Summary Information", "Author"),
            "keywords": ("Inventor Summary Information", "Keywords"),
            "category": ("Inventor Document Summary Information", "Category"),
            "clase_1": ("User Defined Properties", "CLASE 1"),
            "clase_2": ("User Defined Properties", "CLASE 2"),
            "clase_3": ("User Defined Properties", "CLASE 3"),
        }

        try:
            prop_sets = self.doc.PropertySets
            for key, (set_name, prop_name) in prop_map.items():
                if key in properties_to_update:
                    value = properties_to_update[key]
                    try:
                        prop_set = prop_sets.Item(set_name)
                        prop_set.Item(prop_name).Value = value
                    except Exception:
                        # Si la propiedad no existe, intenta crearla (solo para User Defined)
                        if set_name == "User Defined Properties":
                            print(f"INFO: La propiedad '{prop_name}' no existe. Intentando crearla.")
                            prop_set.Add(value, prop_name)
                        else:
                            raise # Vuelve a lanzar la excepción si no es una propiedad de usuario
            print("INFO: Propiedades del documento actualizadas con éxito.")
            return True
        except Exception as e:
            print(f"ERROR al actualizar propiedades: {e}")
            return False

    def save_document(self):
        """
        Guarda el documento activo de Inventor.
        
        Returns:
            bool: True si se guardó correctamente, False en caso de error.
        """
        if self.doc:
            self.doc.Save()
            print("INFO: Documento de Inventor guardado.")
            return True
        return False

    def set_isometric_view(self):
        """
        Ajusta la vista activa del documento a una perspectiva isométrica estándar
        y fuerza la actualización de la pantalla.
        """
        # Aseguramos tener la referencia al documento que está activo AHORA MISMO.
        self.doc = self.app.ActiveDocument if self.app else None

        if not self.doc:
            print("ADVERTENCIA: No hay documento activo para ajustar la vista.")
            return

        try:
            view = self.app.ActiveView
            camera = view.Camera

            # --- Adaptación de la lógica antigua para "despertar" la vista ---
            # 1. Hacemos un cambio de vista preliminar (ej. a Frontal) para asegurar que la UI responda.
            # kFrontViewOrientation = 10761
            camera.ViewOrientationType = 10761
            camera.ApplyWithoutTransition()

            # 2. Ahora establecemos la vista isométrica deseada.
            # kIsoTopRightViewOrientation = 10760
            camera.ViewOrientationType = 10760
            camera.Fit()

            # 3. Aplicamos el cambio final y forzamos la actualización de la pantalla.
            camera.ApplyWithoutTransition()
            view.Update()

            # 4. Damos tiempo a la UI para procesar el redibujado.
            if self.q_app:
                self.q_app.processEvents()

            print("INFO: Vista de Inventor ajustada a perspectiva isométrica.")
        except Exception as e:
            print(f"ERROR: No se pudo ajustar la vista isométrica. Error: {e}")

    def capture_preview_image(self, image_path):
        """
        Captura la vista actual del documento activo y la guarda como una imagen.

        Args:
            image_path (str): La ruta completa del archivo donde se guardará la imagen.
        
        Raises:
            Exception: Si no hay un documento activo o si ocurre un error durante la captura.
        """
        if not self.doc:
            raise Exception("No hay documento activo para capturar la imagen.")
        
        # Ajustamos la vista a la posición estándar antes de capturar
        self.set_isometric_view()
        
        view = self.app.ActiveView
        view.SaveAsBitmap(image_path, 300, 300)

    def get_bom_data(self):
        """
        Extrae la lista de materiales (BoM) estructurada del ensamblaje activo.
        """
        if not self.doc or self.doc.DocumentType not in [12802, 12803]: # kAssemblyDocumentObject, kPresentationDocumentObject
            print("ADVERTENCIA: No hay un ensamblaje activo para obtener la BoM.")
            return []

        bom = self.doc.ComponentDefinition.BOM
        bom.StructuredViewEnabled = True
        bom.StructuredViewFirstLevelOnly = False
        bom_view = bom.BOMViews.Item("Structured")
        
        return self._traverse_bom(bom_view.BOMRows)

    def _traverse_bom(self, bom_rows):
        """
        Función auxiliar recursiva para recorrer las filas de la BoM.

        Args:
            bom_rows: Una colección de filas de la BoM de Inventor.

        Returns:
            list: Una lista de diccionarios, cada uno representando un componente.
        """
        components = []
        for row in bom_rows:
            try:
                component_def = row.ComponentDefinitions.Item(1)
                doc = component_def.Document
                part_number = doc.PropertySets.Item("Design Tracking Properties").Item("Part Number").Value
                
                components.append({
                    'part_number': part_number,
                    'quantity': row.ItemQuantity
                })

                if row.ChildRows:
                    components.extend(self._traverse_bom(row.ChildRows))
            except Exception as e:
                print(f"ADVERTENCIA: No se pudo procesar una fila de la BoM. Error: {e}")
        return components