"""
Módulo de servicio para la conversión de Unidades de Medida (UoM).

Este servicio se conecta a Odoo para obtener un mapa de las unidades de medida y
sus factores de conversión. Permite conversiones precisas entre diferentes
unidades dentro de la misma categoría (ej. de 'mm' a 'cm').
"""
class UnitService:
    """
    Gestiona la lógica de conversión de unidades de medida (UoM)
    basándose en la configuración de Odoo.
    """
    def __init__(self, odoo_api_instance):
        """
        Inicializa el servicio de unidades.

        Args:
            odoo_api_instance (OdooApi): Una instancia conectada de la API de Odoo.
        """
        self.odoo_api = odoo_api_instance
        # El mapa almacena: {nombre_unidad_limpio: {'id', 'name', 'category_id', 'factor', 'uom_type'}}
        self.uom_map = {}
        self._build_uom_map()

    def _build_uom_map(self):
        """
        Construye un mapa en memoria de todas las unidades de medida de Odoo.

        Este mapa se utiliza para realizar conversiones sin necesidad de consultar
        a Odoo en cada operación.
        """
        if not self.odoo_api:
            print("ERROR [UnitService]: No hay conexión a Odoo para construir el mapa de unidades.")
            return

        try:
            # Leemos todas las unidades, sus categorías y factores de conversión.
            uoms = self.odoo_api.execute_kw(
                'uom.uom', 'search_read', [[]],
                {'fields': ['id', 'name', 'category_id', 'uom_type', 'factor']}
            )
            for uom in uoms:
                # Normalizamos el nombre de la unidad para que las búsquedas sean consistentes.
                uom_name_clean = uom['name'].lower().strip()
                self.uom_map[uom_name_clean] = {
                    'id': uom['id'],
                    'category_id': uom['category_id'][0],
                    'name': uom['name'],
                    'uom_type': uom['uom_type'],
                    'factor': uom['factor']
                }
            print("INFO [UnitService]: Mapa de unidades de medida construido exitosamente.")
        except Exception as e:
            print(f"ERROR [UnitService]: Fallo al construir el mapa de unidades: {e}")

    def get_uom_info(self, uom_name):
        """Busca información de una UdM por su nombre en el mapa local."""
        return self.uom_map.get(uom_name.lower().strip())

    def _to_reference_unit(self, quantity, uom_info):
        """Convierte una cantidad a la unidad de referencia de su categoría."""
        if not uom_info or uom_info.get('factor', 0) == 0:
            return quantity

        uom_type = uom_info['uom_type']
        factor = uom_info['factor']

        if uom_type == 'bigger':
            return quantity * factor
        if uom_type == 'smaller':
            return quantity / factor
        # Si es 'reference', no se hace nada
        return quantity

    def _from_reference_unit(self, quantity, uom_info):
        """Convierte una cantidad desde la unidad de referencia a la unidad especificada."""
        if not uom_info or uom_info.get('factor', 0) == 0:
            return quantity

        uom_type = uom_info['uom_type']
        factor = uom_info['factor']

        if uom_type == 'bigger':
            return quantity / factor
        if uom_type == 'smaller':
            return quantity * factor
        # Si es 'reference', no se hace nada
        return quantity

    def convert(self, quantity, from_unit_name, to_unit_name):
        """
        Convierte una cantidad de una unidad de origen a una unidad de destino.

        Args:
            quantity (float): La cantidad numérica a convertir.
            from_unit_name (str): El nombre de la unidad de origen (ej. "mm").
            to_unit_name (str): El nombre de la unidad de destino (ej. "cm").

        Returns:
            float: La cantidad convertida. Si las unidades no son compatibles o
                   no se encuentran, devuelve la cantidad original y muestra una advertencia.
        """
        from_unit_info = self.get_uom_info(from_unit_name)
        to_unit_info = self.get_uom_info(to_unit_name)

        if not from_unit_info:
            print(f"ADVERTENCIA [UnitService]: Unidad de origen '{from_unit_name}' no encontrada. No se realizará la conversión.")
            return quantity

        if not to_unit_info:
            print(f"ADVERTENCIA [UnitService]: Unidad de destino '{to_unit_name}' no encontrada. No se realizará la conversión.")
            return quantity

        # Si las unidades son las mismas, no hay nada que hacer.
        if from_unit_info['id'] == to_unit_info['id']:
            return quantity

        # Validar que ambas unidades pertenezcan a la misma categoría.
        if from_unit_info['category_id'] != to_unit_info['category_id']:
            print(f"ERROR [UnitService]: No se puede convertir de '{from_unit_name}' a '{to_unit_name}' porque pertenecen a categorías diferentes. No se realizará la conversión.")
            return quantity

        # Paso 1: Convertir la cantidad de origen a la unidad de referencia de la categoría.
        value_in_ref_unit = self._to_reference_unit(quantity, from_unit_info)

        # Paso 2: Convertir desde la unidad de referencia a la cantidad de destino.
        final_value = self._from_reference_unit(value_in_ref_unit, to_unit_info)

        return final_value