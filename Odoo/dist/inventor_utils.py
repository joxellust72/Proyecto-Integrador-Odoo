# Primero, intentamos importar el módulo de simulación para tenerlo listo
try:
    from inventor_mock import get_inventor_app as get_mock_app
    MOCK_AVAILABLE = True
except ImportError:
    MOCK_AVAILABLE = False

def get_inventor_app():
    """
    Intenta obtener la instancia real de Inventor. Si falla o no está disponible,
    recurre a la instancia simulada (mock).
    """
    try:
        # Intenta importar y usar la biblioteca real de Inventor
        import win32com.client
        print("Intentando conectar con la instancia real de Inventor...")
        app = win32com.client.GetActiveObject("Inventor.Application")
        print("Conexión con Inventor exitosa.")
        return app
    except Exception as e:
        # Si la conexión real falla (por cualquier motivo)
        print(f"ERROR al conectar con Inventor: {e}")
        if MOCK_AVAILABLE:
            print("Cambiando a modo de simulación.")
            # Llama a la función del mock para obtener la app simulada
            return get_mock_app()
        else:
            print("ERROR CRÍTICO: El modo de simulación (inventor_mock.py) no está disponible.")
            return None

def get_assembly_components(app):
    """Obtiene los componentes del ensamblaje activo."""
    if not app or not app.ActiveDocument:
        return []
    
    definition = app.ActiveDocument.ComponentDefinition
    components = []
    for occ in definition.Occurrences:
        # Extraemos la información relevante de cada 'occurrence'
        component_info = {
            "name": occ.Name,
            "definition_name": occ.Definition.Name,
            "visible": occ.Visible
        }
        components.append(component_info)
    return components
