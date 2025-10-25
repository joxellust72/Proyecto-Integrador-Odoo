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
            print("ERROR [UnitService]: No hay conexión a Odoo para construir el mapa de unidades. El servicio no funcionará correctamente.")
            return

        try:
            # Leemos todas las unidades, sus categorías y factores de conversión.
            uoms = self.odoo_api.execute_kw(
                'uom.uom', 'search_read', [[]],
                {'fields': ['id', 'name', 'category_id', 'uom_type', 'factor', 'rounding']}
            )

            # --- PASO 1: Recolección Exhaustiva (Sin Sobrescribir) ---
            # Creamos un mapa temporal donde cada nombre de unidad puede tener múltiples definiciones
            # si existen unidades con el mismo nombre en diferentes categorías.
            temp_uom_map = {}
            for uom in uoms:
                # Normalizamos el nombre de la unidad para que las búsquedas sean consistentes.
                uom_name_clean = uom['name'].lower().strip()
                uom_data = {
                    'id': uom['id'],
                    'category_id': uom['category_id'][0], # El ID numérico
                    'category_name': uom['category_id'][1].lower().strip(), # El nombre de la categoría (aseguramos minúsculas y sin espacios)
                    'name': uom['name'],
                    'uom_type': uom['uom_type'],
                    'factor': uom['factor'],
                    'rounding': uom['rounding']
                }
                if uom_name_clean not in temp_uom_map:
                    temp_uom_map[uom_name_clean] = []
                temp_uom_map[uom_name_clean].append(uom_data)
            
            # Mostrar el mapa temporal para depuración, como se solicitó.
            print("\n--- INICIO: Mapa Temporal de Unidades de Odoo (temp_uom_map) ---")
            for name, uom_list in temp_uom_map.items():
                print(f"  '{name}': [")
                for uom_info in uom_list:
                    print(f"    {{'id': {uom_info['id']}, 'name': '{uom_info['name']}', 'category_name': '{uom_info['category_name']}'}}")
                print("  ]")
            print("--- FIN: Mapa Temporal de Unidades de Odoo ---\n")

            # --- PASO 2: Filtrado y Selección Inteligente ---
            # Definimos un orden de prioridad para las categorías. Las más específicas y deseables primero.
            # 'unsorted' no está aquí, lo que significa que tendrá la prioridad más baja (float('inf')).
            CATEGORY_PRIORITY = {
                'weight': 1,
                'length / distance': 2,
                'unit': 3,
                'working time': 4, # Añadimos 'working time' como categoría válida
            }

            for uom_name_clean, uom_list in temp_uom_map.items():
                best_uom = None
                best_priority = float('inf') # Prioridad inicial muy baja

                for uom_info in uom_list:
                    category_name = uom_info['category_name']
                    # Asignamos una prioridad muy baja a categorías no definidas o 'unsorted'
                    current_priority = CATEGORY_PRIORITY.get(category_name, float('inf'))

                    if current_priority < best_priority:
                        best_priority = current_priority
                        best_uom = uom_info
                    elif current_priority == best_priority and best_uom is not None:
                        # Ambiguity: Multiple units with the same name and same highest priority category.
                        raise ValueError(
                            f"ERROR [UnitService]: Ambiguity detectada para la unidad '{uom_name_clean}'. "
                            f"Múltiples definiciones encontradas en la misma categoría de alta prioridad '{category_name}'. "
                            "Por favor, corrija la configuración de unidades en Odoo."
                        )
                
                # Si después de la selección, encontramos una unidad válida (con una categoría prioritaria), la añadimos al mapa.
                # Si no, simplemente la ignoramos y continuamos, en lugar de lanzar un error.
                if best_uom and best_priority != float('inf'):
                    self.uom_map[uom_name_clean] = best_uom
                else:
                    print(f"INFO [UnitService]: Ignorando unidad '{uom_name_clean}' por tener categoría no prioritaria ('{uom_list[0]['category_name']}').")

            print("INFO [UnitService]: Mapa de unidades de medida construido y saneado exitosamente.")
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
            # --- LÓGICA DE RESCATE (COMENTADA PARA PRUEBAS - ELIMINAR SI TODO FUNCIONA CORRECTAMENTE) ---
            # Esta sección se usaba para conversiones manuales entre categorías no compatibles en Odoo.
            # Con la nueva lógica de _build_uom_map, esto debería indicar un problema de configuración real en Odoo
            # o un intento de conversión lógicamente incorrecta (ej. kg a metros).
            print(f"ERROR [UnitService]: Las unidades '{from_unit_name}' (categoría '{from_unit_info['category_name']}') y '{to_unit_name}' (categoría '{to_unit_info['category_name']}') no pertenecen a la misma categoría en Odoo y no son compatibles para la conversión.")
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