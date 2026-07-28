from database.database import agregar_gasto


def registrar_gasto(monto, descripcion, categoria="Otros", fecha=None):
    agregar_gasto(monto, descripcion, categoria)
    return True
