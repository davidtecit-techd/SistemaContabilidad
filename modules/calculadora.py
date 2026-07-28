from __future__ import annotations

import calendar
from datetime import date

from database.database import periodo_actual, totales_del_periodo


def resumen_mensual(periodo: str | None = None) -> dict[str, float | int | str]:
    periodo = periodo or periodo_actual()
    anio, mes = map(int, periodo.split("-"))
    ingresos, gastos = totales_del_periodo(periodo)
    dias = calendar.monthrange(anio, mes)[1]
    return {"periodo": periodo, "ingresos": ingresos, "gastos": gastos, "balance": ingresos - gastos, "meta_diaria": gastos / dias, "dias_mes": dias}


def etiqueta_periodo(periodo: str) -> str:
    anio, mes = map(int, periodo.split("-"))
    nombres = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
    return f"{nombres[mes - 1].capitalize()} {anio}"
