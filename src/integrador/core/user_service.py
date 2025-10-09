"""
Módulo de servicio para la gestión de datos de usuario.

Proporciona una forma centralizada de mapear las credenciales de inicio de sesión
(como el correo electrónico) a información más legible para el usuario (como el nombre completo).
"""

# Mapeo centralizado de correos electrónicos a nombres de usuario.
# Para añadir o modificar un usuario, solo es necesario editar este diccionario.
USER_MAP = {
    "admin@automate-corp.com": "Administrador",
    "it@automate-corp.com": "Juan Andres Ruiz Castañeda",
    "ingenieria@automate-corp.com": "Jhoan Sebastian Gaviria",
    "ingenieria1@automate-corp.com": "Jesus Alberto Ariza",
    "ingenieria2@automate-corp.com": "Juan Alejandro Villamizar",
    "ingenieria3@automate-corp.com": "Daniel Jaramillo Vargas",
    "ingenieria5@automate-corp.com": "Alejandro Vargas Lopez",
    "ingenieria6@automate-corp.com": "Andres Felipe Soto Cuellar",
    "ingenieria7@automate-corp.com": "Jhoan Sebastian Isaza",
    "ingenieria8@automate-corp.com": "Julian Mateo Tarazona Arango",
    "electricos1@automate-corp.com": "Julian Andres Chica",
    "electricos2@automate-corp.com": "Luis Fernando Blum Mendoza",
    "automatizacion@automate-corp.com": "Manuel Esteban Contreras",
    "automatizacion2@automate-corp.com": "Diego Andres",
    "sistemas@automate-corp.com": "Brayam Alexander Chica Betancur",
    "procesos@automate-corp.com": "Diego Alexander Ceballos"
}

def get_user_full_name(email: str) -> str:
    """
    Busca el nombre completo de un usuario basado en su dirección de correo electrónico.

    Este servicio utiliza un mapa estático para la correspondencia. Si el correo
    electrónico no se encuentra en el mapa, la función devuelve el correo
    electrónico original como valor predeterminado.

    Args:
        email (str): El correo electrónico del usuario a buscar.

    Returns:
        str: El nombre completo del usuario si se encuentra, o el correo
             electrónico original si no.
    """
    return USER_MAP.get(email, email)