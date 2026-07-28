"""Acceso a la base de datos local del sistema de contabilidad."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "sistema.db"


def conectar() -> sqlite3.Connection:
    conexion = sqlite3.connect(DATABASE_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_base_datos() -> None:
    with conectar() as conexion:
        conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS ingresos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monto REAL NOT NULL CHECK (monto >= 0),
                descripcion TEXT NOT NULL DEFAULT '',
                fecha TEXT NOT NULL,
                creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monto REAL NOT NULL CHECK (monto >= 0),
                descripcion TEXT NOT NULL DEFAULT '',
                categoria TEXT NOT NULL DEFAULT 'General',
                fecha TEXT NOT NULL,
                creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def _validar_movimiento(monto: float, descripcion: str, fecha: str) -> tuple[float, str, str]:
    monto = float(monto)
    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero.")
    fecha = fecha.strip()
    date.fromisoformat(fecha)
    return monto, descripcion.strip(), fecha


def agregar_ingreso(monto: float, descripcion: str, fecha: str) -> None:
    monto, descripcion, fecha = _validar_movimiento(monto, descripcion, fecha)
    with conectar() as conexion:
        conexion.execute(
            "INSERT INTO ingresos (monto, descripcion, fecha) VALUES (?, ?, ?)",
            (monto, descripcion, fecha),
        )


def agregar_gasto(monto: float, descripcion: str, categoria: str, fecha: str) -> None:
    monto, descripcion, fecha = _validar_movimiento(monto, descripcion, fecha)
    with conectar() as conexion:
        conexion.execute(
            "INSERT INTO gastos (monto, descripcion, categoria, fecha) VALUES (?, ?, ?, ?)",
            (monto, descripcion, categoria.strip() or "General", fecha),
        )


def listar_movimientos(tipo: str, limite: int | None = None) -> list[sqlite3.Row]:
    if tipo not in {"ingresos", "gastos"}:
        raise ValueError("Tipo de movimiento no válido.")
    consulta = f"SELECT * FROM {tipo} ORDER BY fecha DESC, id DESC"
    parametros: tuple[int, ...] = ()
    if limite:
        consulta += " LIMIT ?"
        parametros = (limite,)
    with conectar() as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def eliminar_movimiento(tipo: str, movimiento_id: int) -> None:
    if tipo not in {"ingresos", "gastos"}:
        raise ValueError("Tipo de movimiento no válido.")
    with conectar() as conexion:
        conexion.execute(f"DELETE FROM {tipo} WHERE id = ?", (movimiento_id,))


def totales_del_mes(anio: int, mes: int) -> tuple[float, float]:
    inicio = f"{anio:04d}-{mes:02d}-01"
    siguiente = f"{anio + (mes == 12):04d}-{1 if mes == 12 else mes + 1:02d}-01"
    with conectar() as conexion:
        ingresos = conexion.execute(
            "SELECT COALESCE(SUM(monto), 0) FROM ingresos WHERE fecha >= ? AND fecha < ?",
            (inicio, siguiente),
        ).fetchone()[0]
        gastos = conexion.execute(
            "SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE fecha >= ? AND fecha < ?",
            (inicio, siguiente),
        ).fetchone()[0]
    return float(ingresos), float(gastos)
