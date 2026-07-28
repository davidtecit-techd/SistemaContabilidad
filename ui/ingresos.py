from datetime import date

from database.database import agregar_ingreso


def registrar_ingreso(monto, descripcion, fecha=None):
    agregar_ingreso(monto, descripcion, fecha or date.today().isoformat())
    return True
