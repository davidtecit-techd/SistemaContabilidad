from datetime import date

from database.database import agregar_gasto


def registrar_gasto(monto, descripcion, categoria="General", fecha=None):
    agregar_gasto(monto, descripcion, categoria, fecha or date.today().isoformat())
    return True
