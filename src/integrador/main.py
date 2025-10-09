"""
Punto de entrada principal para la aplicación de integración Odoo-Inventor.

Este script se encarga de:
1. Configurar el `sys.path` para asegurar que los módulos del proyecto se encuentren.
2. Determinar si se ejecuta en modo real (conectado a Autodesk Inventor) o en modo simulación.
3. Establecer un manejador global de excepciones para capturar errores inesperados y mostrarlos al usuario.
4. Iniciar la interfaz de usuario principal de la aplicación.
"""
import sys
import os
import win32com.client
import traceback

# Añade el directorio 'src' a la ruta de búsqueda de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from integrador.utils.path_utils import show_error_message

# Intenta obtener la instancia activa de Inventor. Si falla, crea una instancia simulada.
try:
    # Intenta conectarte a la aplicación real de Inventor
    app_instance = win32com.client.GetActiveObject("Inventor.Application")
    print("INFO: Ejecutando en modo real con Autodesk Inventor.")
except Exception:
    print("ADVERTENCIA: No se pudo conectar a Inventor. Cambiando a modo de simulación.")
    from integrador.api.inventor_mock import MockApplication
    app_instance = MockApplication()

# --- Manejador Global de Excepciones ---

def global_exception_hook(exctype, value, tb):
    """
    Captura cualquier excepción no manejada, la muestra en una ventana emergente
    y la imprime en la consola para depuración.
    """
    # Formatear el traceback para que sea legible
    traceback_details = "".join(traceback.format_exception(exctype, value, tb, limit=None, chain=True))
    
    # Mensaje que verá el usuario final.
    error_title = "Error Inesperado en la Aplicación"
    error_message = (
        f"Ha ocurrido un error no controlado:\n\n"
        f"{str(value)}\n\n"
        "Por favor, contacte al soporte técnico con los detalles del error."
    )
    
    # Imprimir el error completo en la consola para el desarrollador.
    print(f"--- ERROR GLOBAL CAPTURADO ---\n{traceback_details}")
    
    # Mostrar el diálogo de error al usuario.
    show_error_message(error_title, error_message, detailed_text=traceback_details)

def main():
    """Función principal que configura e inicia la aplicación."""
    print("INFO: Lanzando el formulario principal de la aplicación.")
    
    # Importamos el módulo de la UI y llamamos a su punto de entrada.
    from integrador.ui import main_window
    main_window.run_app(app_instance)


if __name__ == "__main__":
    # Asignamos nuestra función como el manejador global de excepciones.
    # Esto debe hacerse ANTES de que la aplicación PyQt se inicie por completo.
    sys.excepthook = global_exception_hook
    main()
