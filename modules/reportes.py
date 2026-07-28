from __future__ import annotations

import csv
from pathlib import Path

from database.database import balance_global, listar_movimientos, periodo_actual
from modules.calculadora import etiqueta_periodo, resumen_mensual


def exportar_reporte_mensual(destino: str | Path, periodo: str) -> Path:
    destino = Path(destino)
    resumen = resumen_mensual(periodo)
    with destino.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([f"Reporte mensual: {etiqueta_periodo(periodo)}"])
        escritor.writerow(["Ingresos", resumen["ingresos"]])
        escritor.writerow(["Gastos", resumen["gastos"]])
        escritor.writerow(["Balance", resumen["balance"]])
        escritor.writerow([])
        escritor.writerow(["Fecha", "Tipo", "Descripción", "Categoría", "Monto"])
        filas = []
        for tipo in ("ingresos", "gastos"):
            for movimiento in listar_movimientos(tipo, periodo):
                filas.append((movimiento["fecha"], tipo[:-1].title(), movimiento["descripcion"], movimiento["categoria"] if tipo == "gastos" else "", movimiento["monto"]))
        escritor.writerows(sorted(filas, reverse=True))
    return destino


def exportar_reporte_global(destino: str | Path) -> Path:
    destino = Path(destino)
    ingresos, gastos, balance = balance_global()
    with destino.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["Balance global del negocio"])
        escritor.writerow(["Total ingresos", ingresos])
        escritor.writerow(["Total gastos", gastos])
        escritor.writerow(["Balance", balance])
    return destino


def _pdf_base(destino: str | Path, titulo: str, filas: list[tuple[str, str]]):
    """Genera un PDF sencillo y legible sin cargar ReportLab al abrir la app."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

    destino = Path(destino)
    estilos = getSampleStyleSheet()
    documento = SimpleDocTemplate(str(destino), pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    tabla = Table(filas, colWidths=(9*cm, 6*cm))
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2F3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F9FC")]),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    documento.build([Paragraph(titulo, estilos["Title"]), Spacer(1, 0.5*cm), tabla])
    return destino


def exportar_reporte_mensual_pdf(destino: str | Path, periodo: str) -> Path:
    resumen = resumen_mensual(periodo)
    filas = [("Concepto", "Monto"), ("Ingresos", f"₡{resumen['ingresos']:,.2f}"), ("Gastos", f"₡{resumen['gastos']:,.2f}"), ("Balance", f"₡{resumen['balance']:,.2f}"), ("Meta diaria", f"₡{resumen['meta_diaria']:,.2f}")]
    return _pdf_base(destino, f"Reporte mensual - {etiqueta_periodo(periodo)}", filas)


def exportar_reporte_global_pdf(destino: str | Path) -> Path:
    ingresos, gastos, balance = balance_global()
    filas = [("Concepto", "Monto"), ("Total ingresos", f"₡{ingresos:,.2f}"), ("Total gastos", f"₡{gastos:,.2f}"), ("Balance global", f"₡{balance:,.2f}")]
    return _pdf_base(destino, "Balance global del negocio", filas)
