from __future__ import annotations

import calendar
from datetime import date

from database.database import totales_del_mes


def resumen_mensual(anio: int | None = None, mes: int | None = None) -> dict[str, float | int]:
    hoy = date.today()
    anio, mes = anio or hoy.year, mes or hoy.month
    ingresos, gastos = totales_del_mes(anio, mes)
    dias = calendar.monthrange(anio, mes)[1]
    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "balance": ingresos - gastos,
        "meta_diaria": gastos / dias,
        "dias_mes": dias,
    }
