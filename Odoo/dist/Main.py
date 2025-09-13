import sys
import win32com.client
import traceback
from ui_utils import show_error_message

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

# --- INICIO DEL MANEJADOR GLOBAL DE ERRORES ---
def global_exception_hook(exctype, value, tb):
    """
    Captura cualquier excepción no manejada, la muestra en una ventana emergente
    y la imprime en la consola para depuración.
    """
    # Formatear el traceback para que sea legible
    traceback_details = "".join(traceback.format_exception(exctype, value, tb))
    
    error_title = "Error Inesperado en la Aplicación"
    error_message = (
        f"Ha ocurrido un error no controlado:\n\n"
        f"{str(value)}\n\n"
        "Por favor, contacte al soporte técnico con los detalles del error."
    )
    
    print(f"ERROR GLOBAL CAPTURADO:\n{traceback_details}")
    show_error_message(error_title, error_message, detailed_text=traceback_details)
# --- FIN DEL MANEJADOR GLOBAL DE ERRORES ---

def main():
    """Función principal para ejecutar la aplicación."""
    print("INFO: Lanzando el formulario principal de la aplicación.")
    
    # Importamos el módulo del formulario y le pasamos la instancia ya creada
    import LanzarFormulario
    LanzarFormulario.run_app(app_instance)


if __name__ == "__main__":
    # Asignamos nuestra función como el manejador global de excepciones.
    # Esto debe hacerse ANTES de que la aplicación PyQt se inicie por completo.
    sys.excepthook = global_exception_hook
    main()
