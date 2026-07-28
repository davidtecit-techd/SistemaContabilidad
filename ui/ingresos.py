from database.database import agregar_ingreso


def registrar_ingreso(monto, descripcion, fecha=None):
    # La fecha se toma del calendario del equipo para mantener el período mensual correcto.
    agregar_ingreso(monto, descripcion)
    return True
