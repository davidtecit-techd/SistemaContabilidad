"""Persistencia local y control de períodos mensuales."""

from __future__ import annotations

import sqlite3
import shutil
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "sistema.db"
DEFAULT_CATEGORIES = ("Alquiler", "Servicios públicos", "Insumos", "Marketing", "Mantenimiento", "Salarios", "Impuestos", "Otros")


def periodo_actual() -> str:
    return date.today().strftime("%Y-%m")


@contextmanager
def conectar():
    conexion = sqlite3.connect(DATABASE_PATH)
    conexion.row_factory = sqlite3.Row
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def _columna_existe(conexion: sqlite3.Connection, tabla: str, columna: str) -> bool:
    return columna in {fila["name"] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}


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
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE
            );
            CREATE TABLE IF NOT EXISTS reportes_mensuales (
                periodo TEXT PRIMARY KEY,
                ingresos REAL NOT NULL,
                gastos REAL NOT NULL,
                balance REAL NOT NULL,
                generado_en TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                cantidad INTEGER NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
                costo_unitario REAL NOT NULL DEFAULT 0 CHECK (costo_unitario >= 0),
                actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS gastos_recurrentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                categoria TEXT NOT NULL,
                monto REAL NOT NULL CHECK (monto > 0),
                activo INTEGER NOT NULL DEFAULT 1
            );
            """
        )
        for tabla in ("ingresos", "gastos"):
            if not _columna_existe(conexion, tabla, "periodo"):
                conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN periodo TEXT")
            conexion.execute(f"UPDATE {tabla} SET periodo = substr(fecha, 1, 7) WHERE periodo IS NULL OR periodo = ''")
        if not _columna_existe(conexion, "gastos", "gasto_recurrente_id"):
            conexion.execute("ALTER TABLE gastos ADD COLUMN gasto_recurrente_id INTEGER")
        for categoria in DEFAULT_CATEGORIES:
            conexion.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (categoria,))
    actualizar_periodo_activo()


def actualizar_periodo_activo() -> str:
    """Cierra el período anterior y activa el mes del calendario actual."""
    actual = periodo_actual()
    with conectar() as conexion:
        fila = conexion.execute("SELECT valor FROM configuracion WHERE clave = 'periodo_activo'").fetchone()
        anterior = fila["valor"] if fila else None
        if anterior and anterior != actual:
            _guardar_reporte(conexion, anterior)
        conexion.execute(
            "INSERT INTO configuracion (clave, valor) VALUES ('periodo_activo', ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (actual,),
        )
    aplicar_gastos_recurrentes(actual)
    return actual


def _validar_monto(monto: float, descripcion: str) -> tuple[float, str]:
    monto = float(monto)
    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero.")
    return monto, descripcion.strip()


def agregar_ingreso(monto: float, descripcion: str) -> None:
    monto, descripcion = _validar_monto(monto, descripcion)
    hoy = date.today().isoformat()
    with conectar() as conexion:
        conexion.execute("INSERT INTO ingresos (monto, descripcion, fecha, periodo) VALUES (?, ?, ?, ?)", (monto, descripcion, hoy, periodo_actual()))


def agregar_gasto(monto: float, descripcion: str, categoria: str) -> None:
    monto, descripcion = _validar_monto(monto, descripcion)
    categoria = categoria.strip()
    if not categoria:
        raise ValueError("Selecciona una categoría.")
    hoy = date.today().isoformat()
    with conectar() as conexion:
        conexion.execute("INSERT INTO gastos (monto, descripcion, categoria, fecha, periodo) VALUES (?, ?, ?, ?, ?)", (monto, descripcion, categoria, hoy, periodo_actual()))


def editar_movimiento(tipo: str, movimiento_id: int, monto: float, descripcion: str, categoria: str | None = None) -> None:
    if tipo not in {"ingresos", "gastos"}:
        raise ValueError("Tipo de movimiento no válido.")
    monto, descripcion = _validar_monto(monto, descripcion)
    with conectar() as conexion:
        if tipo == "gastos":
            categoria = (categoria or "").strip()
            if not categoria:
                raise ValueError("Selecciona una categoría.")
            conexion.execute("UPDATE gastos SET monto = ?, descripcion = ?, categoria = ? WHERE id = ?", (monto, descripcion, categoria, movimiento_id))
        else:
            conexion.execute("UPDATE ingresos SET monto = ?, descripcion = ? WHERE id = ?", (monto, descripcion, movimiento_id))


def listar_movimientos(tipo: str, periodo: str | None = None) -> list[sqlite3.Row]:
    if tipo not in {"ingresos", "gastos"}:
        raise ValueError("Tipo de movimiento no válido.")
    periodo = periodo or periodo_actual()
    with conectar() as conexion:
        return conexion.execute(f"SELECT * FROM {tipo} WHERE periodo = ? ORDER BY fecha DESC, id DESC", (periodo,)).fetchall()


def obtener_movimiento(tipo: str, movimiento_id: int) -> sqlite3.Row | None:
    with conectar() as conexion:
        return conexion.execute(f"SELECT * FROM {tipo} WHERE id = ?", (movimiento_id,)).fetchone()


def listar_categorias() -> list[str]:
    with conectar() as conexion:
        return [fila["nombre"] for fila in conexion.execute("SELECT nombre FROM categorias ORDER BY nombre COLLATE NOCASE")]


def crear_categoria(nombre: str) -> None:
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("Escribe el nombre de la categoría.")
    try:
        with conectar() as conexion:
            conexion.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
    except sqlite3.IntegrityError as error:
        raise ValueError("Esa categoría ya existe.") from error


def listar_productos() -> list[sqlite3.Row]:
    with conectar() as conexion:
        return conexion.execute("SELECT *, cantidad * costo_unitario AS valor_total FROM productos ORDER BY nombre COLLATE NOCASE").fetchall()


def crear_producto(nombre: str, cantidad: int, costo_unitario: float) -> None:
    nombre = nombre.strip()
    if not nombre:
        raise ValueError("Escribe el nombre del producto.")
    try:
        cantidad = int(cantidad)
        costo_unitario = float(costo_unitario)
    except ValueError as error:
        raise ValueError("Cantidad y costo deben ser números válidos.") from error
    if cantidad < 0 or costo_unitario < 0:
        raise ValueError("Cantidad y costo no pueden ser negativos.")
    try:
        with conectar() as conexion:
            conexion.execute("INSERT INTO productos (nombre, cantidad, costo_unitario, actualizado_en) VALUES (?, ?, ?, ?)", (nombre, cantidad, costo_unitario, datetime.now().isoformat(timespec="seconds")))
    except sqlite3.IntegrityError as error:
        raise ValueError("Ya existe un producto con ese nombre.") from error


def editar_producto(producto_id: int, nombre: str, cantidad: int, costo_unitario: float) -> None:
    nombre = nombre.strip()
    try:
        cantidad = int(cantidad)
        costo_unitario = float(costo_unitario)
    except ValueError as error:
        raise ValueError("Cantidad y costo deben ser números válidos.") from error
    if not nombre or cantidad < 0 or costo_unitario < 0:
        raise ValueError("Revisa el nombre, cantidad y costo.")
    try:
        with conectar() as conexion:
            conexion.execute("UPDATE productos SET nombre = ?, cantidad = ?, costo_unitario = ?, actualizado_en = ? WHERE id = ?", (nombre, cantidad, costo_unitario, datetime.now().isoformat(timespec="seconds"), producto_id))
    except sqlite3.IntegrityError as error:
        raise ValueError("Ya existe un producto con ese nombre.") from error


def total_inventario() -> float:
    with conectar() as conexion:
        return float(conexion.execute("SELECT COALESCE(SUM(cantidad * costo_unitario), 0) FROM productos").fetchone()[0])


def listar_gastos_recurrentes() -> list[sqlite3.Row]:
    with conectar() as conexion:
        return conexion.execute("SELECT * FROM gastos_recurrentes WHERE activo = 1 ORDER BY categoria, descripcion").fetchall()


def crear_gasto_recurrente(descripcion: str, categoria: str, monto: float) -> None:
    monto, descripcion = _validar_monto(monto, descripcion)
    categoria = categoria.strip() or "Otros"
    with conectar() as conexion:
        conexion.execute("INSERT INTO gastos_recurrentes (descripcion, categoria, monto) VALUES (?, ?, ?)", (descripcion, categoria, monto))


def editar_gasto_recurrente(gasto_id: int, descripcion: str, categoria: str, monto: float) -> None:
    monto, descripcion = _validar_monto(monto, descripcion)
    categoria = categoria.strip() or "Otros"
    with conectar() as conexion:
        conexion.execute("UPDATE gastos_recurrentes SET descripcion = ?, categoria = ?, monto = ? WHERE id = ?", (descripcion, categoria, monto, gasto_id))


def aplicar_gastos_recurrentes(periodo: str) -> None:
    """Registra una única vez los gastos mensuales configurados para el período."""
    with conectar() as conexion:
        recurrentes = conexion.execute("SELECT * FROM gastos_recurrentes WHERE activo = 1").fetchall()
        for gasto in recurrentes:
            existe = conexion.execute("SELECT 1 FROM gastos WHERE gasto_recurrente_id = ? AND periodo = ?", (gasto["id"], periodo)).fetchone()
            if not existe:
                conexion.execute("INSERT INTO gastos (monto, descripcion, categoria, fecha, periodo, gasto_recurrente_id) VALUES (?, ?, ?, ?, ?, ?)", (gasto["monto"], gasto["descripcion"], gasto["categoria"], date.today().isoformat(), periodo, gasto["id"]))


def crear_respaldo_si_necesario(dias: int = 7) -> Path | None:
    with conectar() as conexion:
        ultimo = conexion.execute("SELECT valor FROM configuracion WHERE clave = 'ultimo_respaldo'").fetchone()
        ahora = datetime.now()
        if ultimo and (ahora - datetime.fromisoformat(ultimo["valor"])).days < dias:
            return None
        destino = DATABASE_PATH.parent / "backups" / f"sistema_{ahora:%Y%m%d_%H%M%S}.db"
        destino.parent.mkdir(exist_ok=True)
        conexion.commit()
        shutil.copy2(DATABASE_PATH, destino)
        conexion.execute("INSERT INTO configuracion (clave, valor) VALUES ('ultimo_respaldo', ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor", (ahora.isoformat(timespec="seconds"),))
        return destino


def totales_del_periodo(periodo: str) -> tuple[float, float]:
    with conectar() as conexion:
        ingresos = conexion.execute("SELECT COALESCE(SUM(monto), 0) FROM ingresos WHERE periodo = ?", (periodo,)).fetchone()[0]
        gastos = conexion.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE periodo = ?", (periodo,)).fetchone()[0]
    return float(ingresos), float(gastos)


def _guardar_reporte(conexion: sqlite3.Connection, periodo: str) -> None:
    ingresos = float(conexion.execute("SELECT COALESCE(SUM(monto), 0) FROM ingresos WHERE periodo = ?", (periodo,)).fetchone()[0])
    gastos = float(conexion.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE periodo = ?", (periodo,)).fetchone()[0])
    conexion.execute(
        "INSERT INTO reportes_mensuales (periodo, ingresos, gastos, balance, generado_en) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(periodo) DO UPDATE SET ingresos = excluded.ingresos, gastos = excluded.gastos, balance = excluded.balance, generado_en = excluded.generado_en",
        (periodo, ingresos, gastos, ingresos - gastos, datetime.now().isoformat(timespec="seconds")),
    )


def cerrar_mes_actual() -> None:
    with conectar() as conexion:
        _guardar_reporte(conexion, periodo_actual())


def listar_reportes() -> list[sqlite3.Row]:
    with conectar() as conexion:
        return conexion.execute("SELECT * FROM reportes_mensuales ORDER BY periodo DESC").fetchall()


def balance_global() -> tuple[float, float, float]:
    with conectar() as conexion:
        ingresos = float(conexion.execute("SELECT COALESCE(SUM(monto), 0) FROM ingresos").fetchone()[0])
        gastos = float(conexion.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos").fetchone()[0])
    return ingresos, gastos, ingresos - gastos
