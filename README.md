# Integrador Odoo - Inventor

## 1. Descripción General

Esta aplicación de escritorio sirve como un puente entre Autodesk Inventor y el ERP Odoo. Su objetivo principal es estandarizar y automatizar el proceso de creación de nuevos productos (piezas y ensambles) desde el entorno de diseño CAD.

El flujo de trabajo permite a los diseñadores:
1.  Iniciar sesión con sus credenciales de Odoo.
2.  Seleccionar el tipo de producto que están diseñando.
3.  Validar la información del modelo 3D activo en Inventor.
4.  Generar un código de producto único y estandarizado.
5.  Crear el producto en Odoo con todas sus propiedades (peso, material, categoría, etc.).
6.  Actualizar las iProperties del archivo de Inventor con el nuevo código y el ID de Odoo.
7.  Gestionar la Lista de Materiales (BoM) para ensambles y piezas procesadas.

## 2. Estructura del Proyecto

El proyecto está organizado en una estructura modular para separar responsabilidades y facilitar el mantenimiento.

```
e:\ATCOPIAA\
├── src\
│   └── integrador\
│       ├── api\
│       │   ├── inventor_api.py       # Interactúa con Autodesk Inventor.
│       │   ├── inventor_mock.py      # Simula Inventor para el desarrollo (pruebas). (SIN CONTENIDO PARA EVITAR CONFUCIONES)
│       │   └── odoo_api.py           # Interactúa con la API de Odoo.
│       │
│       ├── core\
│       │   ├── auth_service.py       # Lógica de autenticación y sesión.
│       │   ├── product_flow_service.py # Lógica para crear un producto nuevo.
│       │   ├── processed_material_service.py # Lógica para productos "Materia Prima Procesada" (730).
│       │   ├── unit_service.py       # Lógica de conversión de unidades de medida.
│       │   └── user_service.py       # Mapeo de email a nombre de usuario.
│       │
│       ├── ui\
│       │   ├── main_window.py        # Clase principal que orquesta la UI y los servicios.
│       │   ├── bom_window.py         # Ventana para la gestión de la Lista de Materiales (BoM).
│       │   └── components\           # Widgets personalizados (notificaciones, etc.).
│       │
│       ├── utils\
│       │   └── path_utils.py         # Funciones de ayuda (rutas, diálogos de error).
│       │
│       └── main.py                   # Punto de entrada principal de la aplicación.
│
└── resources\
    ├── ui\                         # Archivos .ui de Qt Designer.
    │   ├── FormularioLogin.ui
    │   ├── FormularioGrupo.ui
    │   ├── FormularioOdoo.ui
    │   └── FormularioListaMateriales.ui
    └── images\                     # Imágenes, iconos, etc.
```

## 3. Descripción de Módulos Clave

### `main.py`
*   **Propósito**: Es el primer archivo que se ejecuta.
*   **Contiene**:
    *   Configuración del `sys.path` para que Python encuentre los otros módulos.
    *   Intento de conexión a una instancia activa de Autodesk Inventor. Si falla, carga un "simulador" (`inventor_mock.py`) para poder ejecutar la aplicación sin Inventor.
    *   Un **manejador global de excepciones**: si la aplicación falla por un error inesperado, este lo captura y lo muestra en una ventana de error amigable.
    *   Llama a `main_window.run_app()` para iniciar la interfaz gráfica.

---

### `ui/main_window.py`
*   **Propósito**: Es el cerebro de la aplicación. Actúa como un "orquestador".
*   **Contiene**:
    *   La clase `MainApplication`.
    *   **Inicialización**: Carga todas las ventanas (`.ui`) y los servicios del directorio `core`.
    *   **Conexión de Señales**: Conecta los clics de los botones de todas las ventanas a los métodos correspondientes (ej. `btnIniciarSesion.clicked.connect(...)`).
    *   **Delegación**: No contiene lógica de negocio compleja. Su trabajo es recibir las acciones del usuario (ej. "crear producto") y delegar la tarea al servicio apropiado (ej. `product_flow_service.create_product_in_odoo()`).
    *   **Gestión de Flujo**: Controla qué ventana se muestra en cada momento (Login -> Grupo -> Principal).

---

### `core/auth_service.py`
*   **Propósito**: Encapsula toda la lógica de autenticación y gestión de sesión.
*   **Contiene**:
    *   `login()`: Valida un usuario y contraseña contra Odoo. Si tiene éxito, guarda la sesión.
    *   `logout()`: Cierra la sesión y elimina el archivo de configuración.
    *   `load_session()`: Intenta cargar las credenciales guardadas para un inicio de sesión automático.
    *   Manejo del archivo `config.json` que se guarda en `%LOCALAPPDATA%\IntegradorOdooInventor`.

---

### `core/product_flow_service.py`
*   **Propósito**: Contiene el flujo de negocio para crear un **nuevo producto estándar**.
*   **Contiene**:
    *   `generate_unique_code()`: Crea un código de 13 dígitos que no existe en Odoo, basado en el grupo seleccionado.
    *   `create_product_in_odoo()`: Recopila todos los datos del formulario y los envía a Odoo para crear el registro del producto.
    *   `update_inventor_properties()`: Después de crear el producto en Odoo, actualiza las iProperties del archivo de Inventor (No. de Pieza, ID de Odoo, etc.).

---

### `core/processed_material_service.py`
*   **Propósito**: Maneja el flujo complejo para los productos del tipo "Materia Prima Procesada" (grupo 730).
*   **Contiene**:
    *   Lógica para leer la iProperty `CODIGO SIZFRA` de una pieza en Inventor para identificar el material base.
    *   Métodos para obtener la cantidad requerida de ese material, ya sea por **longitud** (desde `BOMQuantity`) o por **masa**.
    *   Lógica de conversión de unidades compleja, incluyendo el caso de consumir un material por peso a partir de una pieza medida por longitud.
    *   Creación de la Lista de Materiales (BoM) en Odoo para vincular la pieza procesada con su material base.

---

### `core/unit_service.py`
*   **Propósito**: Proporciona una forma centralizada y fiable de convertir unidades de medida.
*   **Contiene**:
    *   Al iniciar, se conecta a Odoo y descarga un mapa de todas las unidades de medida y sus factores de conversión.
    *   `convert()`: Un método que puede convertir una cantidad entre dos unidades cualesquiera (ej. de `mm` a `m`), siempre que pertenezcan a la misma categoría en Odoo.
    *   `convert_weight_with_optimization()`: Un método especial para pesos que evita guardar en Odoo valores muy pequeños (ej. 0.0001 kg), convirtiéndolos a una unidad más apropiada (ej. 0.1 g).

---

### `api/inventor_api.py`
*   **Propósito**: Simplificar la comunicación con Autodesk Inventor.
*   **Contiene**: Métodos "wrapper" que hacen que sea más fácil:
    *   Leer y escribir iProperties (`get_all_properties`, `update_document_properties`).
    *   Guardar el documento (`save_document`).
    *   Capturar una imagen de la vista actual (`capture_preview_image`).
    *   Ajustar la cámara a una vista isométrica (`set_isometric_view`).

---

### `api/odoo_api.py`
*   **Propósito**: Centralizar la comunicación con la API XML-RPC de Odoo.
*   **Contiene**:
    *   Métodos para `connect`, `search`, `read`, `create`, `write`, etc.
    *   Maneja la estructura de las llamadas a la API, haciendo que el resto del código no necesite conocer los detalles de XML-RPC.

---

### `utils/path_utils.py`
*   **Propósito**: Almacenar funciones de ayuda genéricas.
*   **Contiene**:
    *   `resource_path()`: Una función muy importante que calcula la ruta correcta a los archivos de `resources` (como las UI y las imágenes), tanto en el entorno de desarrollo como cuando la aplicación está empaquetada en un `.exe` con PyInstaller.
    *   `show_error_message()`: Muestra un diálogo de error estándar y reutilizable.

Espero que esta documentación te sirva como una excelente guía. ¡Un saludo!
