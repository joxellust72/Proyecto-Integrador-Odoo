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
                    'category_id': uom['category_id'][0], # El ID numérico
                    'category_name': uom['category_id'][1].lower().strip(), # El nombre de la categoría (aseguramos minúsculas y sin espacios)
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

        if uom_type == 'bigger': # ej. kg a g (referencia) -> se multiplica
            return quantity * factor
        if uom_type == 'smaller': # ej. mm a m (referencia) -> se divide
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
            if factor == 0: return quantity # Evitar división por cero
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
                   no se encuentran, devuelve None y muestra una advertencia/error.
        """
        from_unit_info = self.get_uom_info(from_unit_name)
        to_unit_info = self.get_uom_info(to_unit_name)

        if not from_unit_info:
            print(f"ADVERTENCIA [UnitService]: Unidad de origen '{from_unit_name}' no encontrada. No se realizará la conversión.")
            return None

        if not to_unit_info:
            print(f"ADVERTENCIA [UnitService]: Unidad de destino '{to_unit_name}' no encontrada. No se realizará la conversión.")
            return None

        # Si las unidades son las mismas, no hay nada que hacer.
        if from_unit_info['id'] == to_unit_info['id']:
            return quantity

        # Validar que ambas unidades pertenezcan a la misma categoría.
        if from_unit_info['category_id'] != to_unit_info['category_id']:
            print(f"ADVERTENCIA [UnitService]: Las unidades '{from_unit_name}' y '{to_unit_name}' están en categorías diferentes en Odoo. Intentando conversión manual.")
            
            # --- LÓGICA DE RESCATE ---
            # Si la conversión estándar falla por categorías, aplicamos reglas de sentido común.
            from_unit = from_unit_name.lower()
            to_unit = to_unit_name.lower()

            # Conversiones de Peso
            if from_unit == 'g' and to_unit == 'kg': return quantity / 1000.0
            if from_unit == 'kg' and to_unit == 'g': return quantity * 1000.0

            # Conversiones de Longitud
            if from_unit == 'mm' and to_unit == 'm': return quantity / 1000.0
            if from_unit == 'm' and to_unit == 'mm': return quantity * 1000.0
            if from_unit == 'cm' and to_unit == 'm': return quantity / 100.0
            if from_unit == 'm' and to_unit == 'cm': return quantity * 100.0

            # Si ninguna regla de rescate aplica, entonces sí fallamos.
            print(f"ERROR [UnitService]: No se encontró una regla de conversión manual para '{from_unit_name}' -> '{to_unit_name}'. La conversión ha fallado.")
            return None

        # Paso 1: Convertir la cantidad de origen a la unidad de referencia de la categoría.
        value_in_ref_unit = self._to_reference_unit(quantity, from_unit_info)

        # Paso 2: Convertir desde la unidad de referencia a la cantidad de destino.
        final_value = self._from_reference_unit(value_in_ref_unit, to_unit_info)

        return final_value

    def convert_weight_with_optimization(self, quantity, from_unit_name, to_unit_name):
        """
        Convierte una unidad de peso, optimizando la unidad final para evitar
        la pérdida de precisión en Odoo debido a valores muy pequeños.

        Args:
            quantity (float): La cantidad numérica a convertir.
            from_unit_name (str): El nombre de la unidad de peso de origen (ej. "g").
            to_unit_name (str): El nombre de la unidad de peso de destino (ej. "kg").

        Returns:
            tuple: (float: cantidad_final, str: nombre_unidad_final)
        """
        # Primero, convertimos a la unidad de destino solicitada.
        converted_qty = self.convert(quantity, from_unit_name, to_unit_name)

        # Si la conversión falló (ej. categorías diferentes), no podemos continuar.
        if converted_qty is None:
            return None, to_unit_name

        # Si la unidad de destino es 'kg' y el resultado es muy pequeño,
        # intentamos convertirlo a 'g' para mayor precisión.
        if to_unit_name.lower() == 'kg' and 0 < converted_qty < 0.01:
            # Verificamos que 'g' exista en nuestro mapa.
            gram_info = self.get_uom_info('g')
            if gram_info:
                qty_in_grams = self.convert(quantity, from_unit_name, 'g')
                # Devolvemos el valor en gramos si es más legible.
                return qty_in_grams, 'g'

        # Si no, devolvemos la conversión original.
        return converted_qty, to_unit_name