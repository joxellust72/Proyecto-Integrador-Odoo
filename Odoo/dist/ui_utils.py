import tkinter as tk
from tkinter import ttk, messagebox

def create_ui(components):
    """Crea y muestra la interfaz de usuario principal con la lista de componentes."""
    root = tk.Tk()
    root.title("Asistente de Tareas de Inventor")
    root.geometry("600x400")

    # Frame principal
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Etiqueta
    label = ttk.Label(main_frame, text="Componentes del Ensamblaje Activo:")
    label.pack(pady=5, anchor="w")

    # Treeview para mostrar la tabla de componentes
    columns = ("name", "definition_name", "visible")
    tree = ttk.Treeview(main_frame, columns=columns, show="headings")
    
    # Definir encabezados
    tree.heading("name", text="Nombre de Ocurrencia")
    tree.heading("definition_name", text="Nombre de Definición")
    tree.heading("visible", text="Visible")

    # Añadir los datos de los componentes al Treeview
    for comp in components:
        tree.insert("", tk.END, values=(comp['name'], comp['definition_name'], comp['visible']))

    tree.pack(fill=tk.BOTH, expand=True)

    # Botón de salida
    exit_button = ttk.Button(main_frame, text="Salir", command=root.destroy)
    exit_button.pack(pady=10, side=tk.RIGHT)

    # Iniciar el bucle principal de la UI
    root.mainloop()

def show_info(title, message):
    """Muestra una ventana emergente de información."""
    # Usamos Tkinter para mostrar el mensaje, ya que es nuestra librería de UI
    root = tk.Tk()
    root.withdraw()  # Ocultamos la ventana principal vacía
    messagebox.showinfo(title, message)
    root.destroy()
