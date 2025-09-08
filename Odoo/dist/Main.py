import sys
import win32com.client

# --- Bloque de Simulación y Conexión ---
# Este bloque es la clave. Intenta obtener la instancia real.
# Si falla, crea una instancia simulada.
try:
    # Intenta conectarte a la aplicación real de Inventor
    app_instance = win32com.client.GetActiveObject("Inventor.Application")
    print("INFO: Ejecutando en modo real con Autodesk Inventor.")
except Exception:
    print("ADVERTENCIA: No se pudo conectar a Inventor. Cambiando a modo de simulación.")
    # Si falla, importa y crea una instancia de nuestra aplicación simulada
    from inventor_mock import MockApplication
    app_instance = MockApplication()
# --- Fin del Bloque ---


def main():
    """Función principal para ejecutar la aplicación."""
    print("INFO: Lanzando el formulario principal de la aplicación.")
    
    # Importamos el módulo del formulario y le pasamos la instancia ya creada
    import LanzarFormulario
    LanzarFormulario.run_app(app_instance)


if __name__ == "__main__":
    main()
