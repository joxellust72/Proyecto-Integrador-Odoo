"""
Módulo de servicio para el flujo de "Materia Prima Procesada" (Grupo 730).

Encapsula la lógica para leer un material base desde Inventor, validar su
cantidad (longitud o masa), realizar conversiones de unidades complejas y
crear la línea de BoM correspondiente en Odoo.
"""
from PyQt6.QtWidgets import QMessageBox

class ProcessedMaterialService:
    """Gestiona la lógica de creación de BoM para productos del grupo 730."""

    def __init__(self, odoo_api, inventor_api, unit_service, main_window):
        """
        Inicializa el servicio.

        Args:
            odoo_api (OdooApi): Instancia de la API de Odoo.
            inventor_api (InventorApi): Instancia de la API de Inventor.
            unit_service (UnitService): Instancia del servicio de unidades.
            main_window: Referencia a la ventana principal de la UI.
        """
        self.odoo_api = odoo_api
        self.inventor_api = inventor_api
        self.unit_service = unit_service
        self.main_window = main_window
        
        # Estado interno para la cantidad leída de Inventor
        self._current_base_material_qty = 0.0
        self._current_base_material_unit = ""

    def get_base_material_from_inventor(self):
        """
        Lee la iProperty 'CODIGO SIZFRA' de Inventor, busca el producto en Odoo
        y actualiza el formulario.
        """
        try:
            codigo_sizfra = self.inventor_api._get_property("User Defined Properties", "CODIGO SIZFRA")
            if not codigo_sizfra:
                QMessageBox.critical(self.main_window, "Error", "La iProperty 'CODIGO SIZFRA' no puede estar vacía.")
                return False

            codigo_sizfra = str(int(float(codigo_sizfra))).strip()
            product = self.odoo_api.execute_kw(
                'product.product', 'search_read',
                [['|', ['default_code', '=', codigo_sizfra], ['barcode', '=', codigo_sizfra]]],
                {'fields': ['id', 'name', 'default_code'], 'limit': 1}
            )

            if not product:
                QMessageBox.critical(self.main_window, "Error de Búsqueda", f"No se encontró material base en Odoo con el código '{codigo_sizfra}'.")
                return False

            self.main_window.txtMaterialBase_integrado.setText(product[0].get('default_code') or codigo_sizfra)
            self.main_window.lblMensaje_3.setText(f"Material base '{product[0]['name']}' cargado.")
            return True
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error de Inventor", f"No se pudo leer la propiedad 'CODIGO SIZFRA'. Error: {e}")
            return False

    def get_base_material_quantity(self, required_category=None):
        """Determina la cantidad del material base desde Inventor (longitud o masa)."""
        qty_found = False
        self._current_base_material_qty = 0.0
        self._current_base_material_unit = ""

        # Prioridad 1: BOMQuantity (Longitud)
        if required_category in ['length / distance', None]:
            try:
                bom_quantity_str = self.inventor_api.doc.ComponentDefinition.BOMQuantity.UnitQuantity
                if bom_quantity_str and "cada una" not in bom_quantity_str.lower():
                    value_str = ''.join(filter(lambda x: x.isdigit() or x in ',.', bom_quantity_str))
                    unit_str = ''.join(filter(str.isalpha, bom_quantity_str))
                    if value_str and unit_str:
                        value = float(value_str.replace(',', '.'))
                        if value > 0:
                            self._current_base_material_qty = value
                            self._current_base_material_unit = unit_str.strip().lower()
                            self.main_window.txtCantReq_integrado.setText(f"{value} {self._current_base_material_unit}")
                            qty_found = True
            except Exception:
                pass # Falla silenciosamente para intentar con la masa

        # Prioridad 2: Masa (Peso)
        if not qty_found or required_category == 'weight':
            mass_in_grams = self.inventor_api._get_property("Design Tracking Properties", "Mass", 0.0)
            if mass_in_grams > 0:
                self._current_base_material_qty = mass_in_grams
                self._current_base_material_unit = "g"
                display_qty, display_unit = (mass_in_grams / 1000, "kg") if mass_in_grams >= 1000 else (mass_in_grams, "g")
                self.main_window.txtCantReq_integrado.setText(f"{display_qty:.4f} {display_unit}")
                qty_found = True

        if not qty_found:
            QMessageBox.critical(self.main_window, "Cantidad no encontrada", "No se encontró una cantidad válida (Longitud o Masa).")
            return False
        
        self.main_window.txtCantReq_integrado.setReadOnly(True)
        return True

    def create_bom_for_product(self):
        """Orquesta la creación de la BoM para el producto procesado."""
        parent_product_id = self.main_window.property("current_parent_product_id")
        if not parent_product_id:
            QMessageBox.critical(self.main_window, "Error", "No se ha identificado el producto padre.")
            return False

        # Obtener ID de la plantilla del producto padre
        parent_template_id = self._get_product_template_id(parent_product_id)
        if not parent_template_id:
            return False

        # Obtener ID del material base
        base_material_code = self.main_window.txtMaterialBase_integrado.text().strip()
        base_material_id = self.odoo_api.find_product_by_barcode(base_material_code)
        if not base_material_id:
            QMessageBox.critical(self.main_window, "Error", f"No se encontró el material base '{base_material_code}' en Odoo.")
            return False

        # Obtener info de la UoM de destino (del material base en Odoo)
        uom_data = self.odoo_api.execute_kw('product.product', 'read', [base_material_id], {'fields': ['uom_name']})
        # --- CORRECCIÓN ---
        # Normalizamos el nombre de la unidad a minúsculas y sin espacios para que coincida con las claves del uom_map.
        uom_name_odoo = uom_data[0]['uom_name'].lower().strip()
        uom_info_odoo = self.unit_service.get_uom_info(uom_name_odoo)
        if not uom_info_odoo:
            QMessageBox.critical(self.main_window, "Error", f"La unidad '{uom_name_odoo}' del material base no se encontró.")
            return False

        # Leer la cantidad de Inventor basándose en la categoría de la UoM de Odoo
        if not self.get_base_material_quantity(required_category=uom_info_odoo['category_name'].lower().strip()):
            return False

        # Realizar la conversión de unidades
        cantidad_a_subir, unidad_a_subir_id = self._calculate_final_quantity(uom_info_odoo)
        if cantidad_a_subir is None:
            return False # El error ya fue mostrado en la función de cálculo

        # Crear la BoM y su línea
        bom_id = self._create_bom_header(parent_template_id)
        if not bom_id:
            return False

        return self._create_bom_line(bom_id, base_material_id, cantidad_a_subir, unidad_a_subir_id)

    def _calculate_final_quantity(self, uom_info_odoo):
        """Calcula la cantidad final a subir a Odoo, manejando la conversión entre categorías."""
        uom_name_odoo = uom_info_odoo['name']
        uom_info_inventor = self.unit_service.get_uom_info(self._current_base_material_unit)
        if not uom_info_inventor:
            QMessageBox.critical(self.main_window, "Error de Unidad", f"La unidad '{self._current_base_material_unit}' de Inventor no es válida.")
            return None, None

        cat_inv = uom_info_inventor['category_name'].lower().strip()
        cat_odoo = uom_info_odoo['category_name'].lower().strip()

        is_inv_len = 'length' in cat_inv or 'distance' in cat_inv
        is_odoo_weight = 'weight' in cat_odoo

        # Caso A: Inventor (Longitud) -> Odoo (Peso)
        if is_inv_len and is_odoo_weight:
            mass_in_grams = self.inventor_api._get_property("Design Tracking Properties", "Mass", 0.0)
            if mass_in_grams <= 0:
                QMessageBox.critical(self.main_window, "Masa no encontrada", "La conversión requiere la masa de la pieza, pero es cero.")
                return None, None
            qty, uom_name = self.unit_service.convert_weight_with_optimization(mass_in_grams, "g", uom_name_odoo)
            uom_id = self.unit_service.get_uom_info(uom_name)['id']
            return qty, uom_id

        # Caso C (Bloqueado): Inventor (Peso) -> Odoo (Longitud)
        if 'weight' in cat_inv and ('length' in cat_odoo or 'distance' in cat_odoo):
            QMessageBox.critical(self.main_window, "Error de Lógica", "No se puede consumir un material medido por Longitud a partir de una pieza cuya cantidad es su Peso.")
            return None, None

        # Casos B y D (Compatibles): Long->Long, Peso->Peso
        if cat_inv == cat_odoo:
            if 'weight' in cat_inv: # Peso -> Peso
                qty, uom_name = self.unit_service.convert_weight_with_optimization(self._current_base_material_qty, self._current_base_material_unit, uom_name_odoo)
                uom_id = self.unit_service.get_uom_info(uom_name)['id']
                return qty, uom_id
            else: # Long -> Long u otro
                qty = self.unit_service.convert(self._current_base_material_qty, self._current_base_material_unit, uom_name_odoo)
                return qty, uom_info_odoo['id']

        # Si las categorías no son compatibles y no es el Caso A
        QMessageBox.critical(self.main_window, "Error de Compatibilidad", f"Las unidades no son compatibles para la conversión: de '{cat_inv}' a '{cat_odoo}'.")
        return None, None

    def _get_product_template_id(self, product_id):
        """Obtiene el ID de product.template a partir de un ID de product.product."""
        data = self.odoo_api.execute_kw('product.product', 'read', [product_id], {'fields': ['product_tmpl_id']})
        if not data or not data[0].get('product_tmpl_id'):
            QMessageBox.critical(self.main_window, "Error", f"No se encontró la plantilla para el producto ID: {product_id}.")
            return None
        return data[0]['product_tmpl_id'][0]

    def _create_bom_header(self, template_id):
        """Crea una nueva cabecera de BoM."""
        bom_id = self.odoo_api.execute_kw('mrp.bom', 'create', [{'product_tmpl_id': template_id, 'product_qty': 1, 'consumption': 'flexible'}])
        if not bom_id:
            QMessageBox.critical(self.main_window, "Error", "No se pudo crear la lista de materiales.")
            return None
        return bom_id[0] if isinstance(bom_id, list) else bom_id

    def _create_bom_line(self, bom_id, material_id, quantity, uom_id):
        """Crea una línea en una BoM existente."""
        line_vals = {'bom_id': bom_id, 'product_id': material_id, 'product_qty': quantity, 'product_uom_id': uom_id}
        line_id = self.odoo_api.execute_kw('mrp.bom.line', 'create', [line_vals])
        if not line_id:
            QMessageBox.critical(self.main_window, "Error", "No se pudo crear la línea de la lista de materiales.")
            return False
        
        created_id = line_id[0] if isinstance(line_id, list) else line_id
        print(f"INFO: Línea de BoM creada con ID: {created_id}")
        return True