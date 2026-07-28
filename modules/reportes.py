from __future__ import annotations

import csv
from pathlib import Path

from database.database import listar_movimientos
from modules.calculadora import resumen_mensual


def exportar_csv(destino: str | Path) -> Path:
    destino = Path(destino)
    filas = []
    for tipo in ("ingresos", "gastos"):
        for movimiento in listar_movimientos(tipo):
            filas.append((movimiento["fecha"], tipo[:-1].title(), movimiento["descripcion"], movimiento["categoria"] if tipo == "gastos" else "", movimiento["monto"]))
    filas.sort(reverse=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["Fecha", "Tipo", "Descripción", "Categoría", "Monto"])
        escritor.writerows(filas)
    return destino


def texto_resumen() -> str:
    resumen = resumen_mensual()
    return (
        f"Ingresos: ₡{resumen['ingresos']:,.2f}\n"
        f"Gastos: ₡{resumen['gastos']:,.2f}\n"
        f"Balance: ₡{resumen['balance']:,.2f}\n"
        f"Meta diaria: ₡{resumen['meta_diaria']:,.2f}"
    )
