from __future__ import annotations

from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk

from database.database import (
    agregar_gasto,
    agregar_ingreso,
    actualizar_periodo_activo,
    balance_global,
    cerrar_mes_actual,
    crear_gasto_recurrente,
    crear_producto,
    crear_categoria,
    crear_respaldo_si_necesario,
    editar_gasto_recurrente,
    editar_movimiento,
    editar_producto,
    inicializar_base_datos,
    listar_categorias,
    listar_gastos_recurrentes,
    listar_movimientos,
    listar_productos,
    listar_reportes,
    obtener_movimiento,
    periodo_actual,
    total_inventario,
)
from modules.calculadora import etiqueta_periodo, resumen_mensual
from modules.reportes import exportar_reporte_global, exportar_reporte_global_pdf, exportar_reporte_mensual, exportar_reporte_mensual_pdf


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def moneda(monto: float) -> str:
    return f"₡{monto:,.2f}"


class SistemaContabilidad(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_base_datos()
        crear_respaldo_si_necesario()
        self.periodo = actualizar_periodo_activo()
        self.title("Sistema de Contabilidad")
        self.geometry("1150x740")
        self.minsize(920, 620)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._crear_menu()
        self.contenido = ctk.CTkFrame(self, corner_radius=0)
        self.contenido.grid(row=0, column=1, sticky="nsew")
        self.mostrar_dashboard()

    def _crear_menu(self):
        menu = ctk.CTkFrame(self, width=215, corner_radius=0, fg_color="#132238")
        menu.grid(row=0, column=0, sticky="nsew")
        menu.grid_propagate(False)
        ctk.CTkLabel(menu, text="CONTABILIDAD", font=("Segoe UI", 21, "bold"), text_color="#FFFFFF").pack(pady=(34, 4))
        ctk.CTkLabel(menu, text="Control de tu negocio", text_color="gray70").pack(pady=(0, 26))
        for texto, comando in [
            ("Inicio", self.mostrar_dashboard),
            ("Nuevo ingreso", lambda: self.abrir_formulario("ingresos")),
            ("Nuevo gasto", lambda: self.abrir_formulario("gastos")),
            ("Movimientos del mes", self.mostrar_movimientos),
            ("Categorías", self.mostrar_categorias),
            ("Inventario", self.mostrar_inventario),
            ("Gastos mensuales", self.mostrar_recurrentes),
            ("Reportes", self.mostrar_reportes),
        ]:
            ctk.CTkButton(menu, text=texto, command=comando, width=175, height=37, fg_color="#24476B", hover_color="#2E6396").pack(pady=5)
        ctk.CTkLabel(menu, text="Los reportes se cierran\nautomáticamente cada mes.", justify="center", text_color="gray70").pack(side="bottom", pady=28)

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def _encabezado(self, titulo, subtitulo=""):
        ctk.CTkLabel(self.contenido, text=titulo, font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=35, pady=(30, 3))
        if subtitulo:
            ctk.CTkLabel(self.contenido, text=subtitulo, text_color="gray70").pack(anchor="w", padx=35, pady=(0, 20))

    def mostrar_dashboard(self):
        self.periodo = actualizar_periodo_activo()
        self.limpiar_contenido()
        resumen = resumen_mensual(self.periodo)
        self._encabezado("Panel del mes", f"Período activo: {etiqueta_periodo(self.periodo)}")
        tarjetas = ctk.CTkFrame(self.contenido, fg_color="transparent")
        tarjetas.pack(fill="x", padx=30)
        tarjetas.grid_columnconfigure((0, 1, 2, 3), weight=1)
        datos = (("Ingresos", resumen["ingresos"], "#2ca25f"), ("Gastos", resumen["gastos"], "#e05a5a"), ("Balance", resumen["balance"], "#4a90e2"), ("Meta diaria", resumen["meta_diaria"], "#ae7be4"))
        for columna, (titulo, valor, color) in enumerate(datos):
            tarjeta = ctk.CTkFrame(tarjetas, border_width=1, border_color=color)
            tarjeta.grid(row=0, column=columna, padx=7, sticky="ew")
            ctk.CTkLabel(tarjeta, text=titulo, font=("Segoe UI", 15)).pack(pady=(18, 4))
            ctk.CTkLabel(tarjeta, text=moneda(float(valor)), font=("Segoe UI", 21, "bold"), text_color=color).pack(pady=(0, 18))
        ctk.CTkLabel(self.contenido, text="Movimientos de este mes", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=35, pady=(32, 10))
        self._tabla_movimientos(self.contenido, altura=8)

    def _tabla_movimientos(self, padre, altura=12):
        marco = ctk.CTkFrame(padre)
        marco.pack(fill="both", expand=True, padx=35, pady=(0, 20))
        tabla = ttk.Treeview(marco, columns=("tipo", "fecha", "descripcion", "categoria", "monto"), show="headings", height=altura)
        for clave, texto, ancho in (("tipo", "Tipo", 90), ("fecha", "Fecha", 100), ("descripcion", "Descripción", 285), ("categoria", "Categoría", 155), ("monto", "Monto", 130)):
            tabla.heading(clave, text=texto)
            tabla.column(clave, width=ancho, anchor="e" if clave == "monto" else "w")
        filas = []
        for tipo in ("ingresos", "gastos"):
            for movimiento in listar_movimientos(tipo, self.periodo):
                filas.append((movimiento["fecha"], tipo, movimiento))
        for _, tipo, movimiento in sorted(filas, key=lambda fila: (fila[0], fila[2]["id"]), reverse=True):
            tabla.insert("", "end", iid=f"{tipo}:{movimiento['id']}", values=(tipo[:-1].title(), movimiento["fecha"], movimiento["descripcion"], movimiento["categoria"] if tipo == "gastos" else "—", moneda(movimiento["monto"])))
        tabla.pack(fill="both", expand=True, padx=12, pady=12)
        return tabla

    def abrir_formulario(self, tipo, movimiento=None):
        editar = movimiento is not None
        ventana = ctk.CTkToplevel(self)
        ventana.title("Editar movimiento" if editar else ("Nuevo ingreso" if tipo == "ingresos" else "Nuevo gasto"))
        ventana.geometry("430x340" if tipo == "gastos" else "430x280")
        ventana.transient(self)
        ventana.grab_set()
        accion = "Editar" if editar else "Registrar"
        ctk.CTkLabel(ventana, text=f"{accion} {'ingreso' if tipo == 'ingresos' else 'gasto'}", font=("Segoe UI", 22, "bold")).pack(pady=(24, 18))
        ctk.CTkLabel(ventana, text=f"Se guardará en {etiqueta_periodo(self.periodo)}", text_color="gray70").pack(pady=(0, 12))
        campos = {}
        for clave, etiqueta, ejemplo in (("monto", "Monto", "Ejemplo: 25000"), ("descripcion", "Descripción", "Ejemplo: Venta del día")):
            ctk.CTkLabel(ventana, text=etiqueta).pack(anchor="w", padx=48)
            entrada = ctk.CTkEntry(ventana, placeholder_text=ejemplo, width=335)
            entrada.pack(pady=(2, 10))
            if editar:
                entrada.insert(0, str(movimiento[clave]))
            campos[clave] = entrada
        if tipo == "gastos":
            ctk.CTkLabel(ventana, text="Categoría").pack(anchor="w", padx=48)
            categoria = ctk.CTkComboBox(ventana, values=listar_categorias(), width=335, state="readonly")
            categoria.pack(pady=(2, 15))
            categoria.set(movimiento["categoria"] if editar else (listar_categorias()[0] if listar_categorias() else ""))
            campos["categoria"] = categoria

        def guardar():
            try:
                if editar:
                    editar_movimiento(tipo, movimiento["id"], campos["monto"].get(), campos["descripcion"].get(), campos.get("categoria").get() if tipo == "gastos" else None)
                elif tipo == "ingresos":
                    agregar_ingreso(campos["monto"].get(), campos["descripcion"].get())
                else:
                    agregar_gasto(campos["monto"].get(), campos["descripcion"].get(), campos["categoria"].get())
            except ValueError as error:
                messagebox.showerror("Datos no válidos", str(error), parent=ventana)
                return
            ventana.destroy()
            self.mostrar_movimientos() if editar else self.mostrar_dashboard()

        ctk.CTkButton(ventana, text="Guardar cambios" if editar else "Guardar", command=guardar, width=190).pack(pady=12)

    def mostrar_movimientos(self):
        self.limpiar_contenido()
        self._encabezado("Movimientos del mes", f"Edita los registros de {etiqueta_periodo(self.periodo)}. Los movimientos no se eliminan.")
        tabla = self._tabla_movimientos(self.contenido)
        def editar_seleccionado():
            seleccionado = tabla.selection()
            if not seleccionado:
                messagebox.showinfo("Selecciona un movimiento", "Selecciona una fila para editarla.", parent=self)
                return
            tipo, movimiento_id = seleccionado[0].split(":")
            movimiento = obtener_movimiento(tipo, int(movimiento_id))
            if movimiento:
                self.abrir_formulario(tipo, movimiento)
        ctk.CTkButton(self.contenido, text="Editar movimiento seleccionado", command=editar_seleccionado, width=250).pack(anchor="e", padx=35, pady=(0, 25))

    def mostrar_categorias(self):
        self.limpiar_contenido()
        self._encabezado("Categorías de gastos", "Crea categorías para usarlas siempre al registrar un gasto.")
        marco = ctk.CTkFrame(self.contenido)
        marco.pack(fill="x", padx=35, pady=8)
        entrada = ctk.CTkEntry(marco, placeholder_text="Ejemplo: Barbería e insumos", width=330)
        entrada.pack(side="left", padx=18, pady=18)
        def agregar():
            try:
                crear_categoria(entrada.get())
            except ValueError as error:
                messagebox.showerror("Categoría", str(error), parent=self)
                return
            self.mostrar_categorias()
        ctk.CTkButton(marco, text="Crear categoría", command=agregar).pack(side="left", padx=5)
        lista = ctk.CTkFrame(self.contenido)
        lista.pack(fill="both", expand=True, padx=35, pady=18)
        for indice, categoria in enumerate(listar_categorias()):
            ctk.CTkLabel(lista, text=categoria, anchor="w", font=("Segoe UI", 16)).grid(row=indice, column=0, sticky="ew", padx=18, pady=7)
        lista.grid_columnconfigure(0, weight=1)

    def mostrar_inventario(self):
        self.limpiar_contenido()
        self._encabezado("Inventario", "Administra existencias y el valor total invertido en productos.")
        total = total_inventario()
        tarjeta = ctk.CTkFrame(self.contenido, fg_color="#1F4E78")
        tarjeta.pack(fill="x", padx=35, pady=(0, 16))
        ctk.CTkLabel(tarjeta, text="Valor total del inventario", text_color="#DCEBFA", font=("Segoe UI", 15)).pack(anchor="w", padx=20, pady=(15, 0))
        ctk.CTkLabel(tarjeta, text=moneda(total), text_color="white", font=("Segoe UI", 26, "bold")).pack(anchor="w", padx=20, pady=(2, 15))
        marco = ctk.CTkFrame(self.contenido)
        marco.pack(fill="both", expand=True, padx=35, pady=(0, 8))
        tabla = ttk.Treeview(marco, columns=("nombre", "cantidad", "costo", "total"), show="headings", height=12)
        for clave, texto, ancho in (("nombre", "Producto", 330), ("cantidad", "Cantidad", 120), ("costo", "Costo unitario", 170), ("total", "Valor total", 170)):
            tabla.heading(clave, text=texto); tabla.column(clave, width=ancho, anchor="e" if clave != "nombre" else "w")
        for producto in listar_productos():
            tabla.insert("", "end", iid=str(producto["id"]), values=(producto["nombre"], producto["cantidad"], moneda(producto["costo_unitario"]), moneda(producto["valor_total"])))
        tabla.pack(fill="both", expand=True, padx=12, pady=12)
        botones = ctk.CTkFrame(self.contenido, fg_color="transparent")
        botones.pack(fill="x", padx=35, pady=(0, 24))
        ctk.CTkButton(botones, text="Agregar producto", command=lambda: self.abrir_producto()).pack(side="right")
        def editar():
            seleccionado = tabla.selection()
            if not seleccionado:
                messagebox.showinfo("Selecciona un producto", "Selecciona un producto para editarlo.", parent=self); return
            producto = next((p for p in listar_productos() if p["id"] == int(seleccionado[0])), None)
            if producto: self.abrir_producto(producto)
        ctk.CTkButton(botones, text="Editar producto", command=editar).pack(side="right", padx=10)

    def abrir_producto(self, producto=None):
        editar = producto is not None
        ventana = ctk.CTkToplevel(self); ventana.title("Editar producto" if editar else "Nuevo producto"); ventana.geometry("420x330"); ventana.transient(self); ventana.grab_set()
        ctk.CTkLabel(ventana, text="Inventario", font=("Segoe UI", 22, "bold")).pack(pady=(25, 18))
        campos = {}
        for clave, etiqueta, ejemplo in (("nombre", "Nombre del producto", "Ejemplo: Cera para cabello"), ("cantidad", "Cantidad disponible", "Ejemplo: 12"), ("costo", "Costo unitario", "Ejemplo: 3500")):
            ctk.CTkLabel(ventana, text=etiqueta).pack(anchor="w", padx=43)
            entrada = ctk.CTkEntry(ventana, placeholder_text=ejemplo, width=335); entrada.pack(pady=(2, 10))
            if editar: entrada.insert(0, str(producto["costo_unitario"] if clave == "costo" else producto[clave]))
            campos[clave] = entrada
        def guardar():
            try:
                if editar: editar_producto(producto["id"], campos["nombre"].get(), campos["cantidad"].get(), campos["costo"].get())
                else: crear_producto(campos["nombre"].get(), campos["cantidad"].get(), campos["costo"].get())
            except ValueError as error:
                messagebox.showerror("Inventario", str(error), parent=ventana); return
            ventana.destroy(); self.mostrar_inventario()
        ctk.CTkButton(ventana, text="Guardar", command=guardar, width=180).pack(pady=12)

    def mostrar_recurrentes(self):
        self.limpiar_contenido()
        self._encabezado("Gastos mensuales", "Se registran automáticamente una vez al iniciar cada mes. No necesitas ingresarlos a diario.")
        marco = ctk.CTkFrame(self.contenido); marco.pack(fill="both", expand=True, padx=35, pady=(0, 8))
        tabla = ttk.Treeview(marco, columns=("descripcion", "categoria", "monto"), show="headings", height=12)
        for clave, texto, ancho in (("descripcion", "Descripción", 340), ("categoria", "Categoría", 230), ("monto", "Monto mensual", 180)):
            tabla.heading(clave, text=texto); tabla.column(clave, width=ancho, anchor="e" if clave == "monto" else "w")
        for gasto in listar_gastos_recurrentes(): tabla.insert("", "end", iid=str(gasto["id"]), values=(gasto["descripcion"], gasto["categoria"], moneda(gasto["monto"])))
        tabla.pack(fill="both", expand=True, padx=12, pady=12)
        botones = ctk.CTkFrame(self.contenido, fg_color="transparent"); botones.pack(fill="x", padx=35, pady=(0, 24))
        ctk.CTkButton(botones, text="Agregar gasto mensual", command=lambda: self.abrir_recurrente()).pack(side="right")
        def editar():
            seleccionado = tabla.selection()
            if not seleccionado: messagebox.showinfo("Selecciona un gasto", "Selecciona un gasto mensual para editarlo.", parent=self); return
            gasto = next((g for g in listar_gastos_recurrentes() if g["id"] == int(seleccionado[0])), None)
            if gasto: self.abrir_recurrente(gasto)
        ctk.CTkButton(botones, text="Editar gasto mensual", command=editar).pack(side="right", padx=10)

    def abrir_recurrente(self, gasto=None):
        editar = gasto is not None
        ventana = ctk.CTkToplevel(self); ventana.title("Gasto mensual"); ventana.geometry("430x330"); ventana.transient(self); ventana.grab_set()
        ctk.CTkLabel(ventana, text="Gasto mensual recurrente", font=("Segoe UI", 21, "bold")).pack(pady=(24, 18))
        campos = {}
        for clave, etiqueta, ejemplo in (("descripcion", "Descripción", "Ejemplo: Alquiler"), ("monto", "Monto mensual", "Ejemplo: 250000")):
            ctk.CTkLabel(ventana, text=etiqueta).pack(anchor="w", padx=45)
            entrada = ctk.CTkEntry(ventana, placeholder_text=ejemplo, width=335); entrada.pack(pady=(2, 10))
            if editar: entrada.insert(0, str(gasto[clave]))
            campos[clave] = entrada
        ctk.CTkLabel(ventana, text="Categoría").pack(anchor="w", padx=45)
        categoria = ctk.CTkComboBox(ventana, values=listar_categorias(), width=335, state="readonly"); categoria.pack(pady=(2, 15)); categoria.set(gasto["categoria"] if editar else (listar_categorias()[0] if listar_categorias() else "Otros"))
        def guardar():
            try:
                if editar: editar_gasto_recurrente(gasto["id"], campos["descripcion"].get(), categoria.get(), campos["monto"].get())
                else: crear_gasto_recurrente(campos["descripcion"].get(), categoria.get(), campos["monto"].get())
            except ValueError as error: messagebox.showerror("Gasto mensual", str(error), parent=ventana); return
            ventana.destroy(); self.mostrar_recurrentes()
        ctk.CTkButton(ventana, text="Guardar", command=guardar, width=180).pack(pady=12)

    def mostrar_reportes(self):
        self.limpiar_contenido()
        self._encabezado("Reportes", "Consulta y descarga los meses cerrados, o el período actual cuando lo necesites.")
        global_ingresos, global_gastos, global_balance = balance_global()
        global_frame = ctk.CTkFrame(self.contenido)
        global_frame.pack(fill="x", padx=35, pady=(0, 14))
        ctk.CTkLabel(global_frame, text=f"Balance global: {moneda(global_balance)}", font=("Segoe UI", 20, "bold")).pack(side="left", padx=18, pady=16)
        ctk.CTkLabel(global_frame, text=f"Ingresos {moneda(global_ingresos)}  |  Gastos {moneda(global_gastos)}", text_color="gray70").pack(side="left", padx=5)
        def descargar_global_csv():
            destino = Path(__file__).resolve().parent / "reports" / "balance_global.csv"
            exportar_reporte_global(destino)
            messagebox.showinfo("Reporte global", f"Archivo creado:\n{destino}", parent=self)
        def descargar_global_pdf():
            try:
                destino = Path(__file__).resolve().parent / "reports" / "balance_global.pdf"
                exportar_reporte_global_pdf(destino)
                messagebox.showinfo("Reporte global", f"Archivo creado:\n{destino}", parent=self)
            except ImportError:
                messagebox.showerror("Falta una dependencia", "Instala las dependencias con: py -m pip install -r requirements.txt", parent=self)
        ctk.CTkButton(global_frame, text="PDF global", command=descargar_global_pdf).pack(side="right", padx=(0, 18))
        ctk.CTkButton(global_frame, text="CSV global", command=descargar_global_csv).pack(side="right", padx=8)
        marco = ctk.CTkFrame(self.contenido)
        marco.pack(fill="both", expand=True, padx=35, pady=(0, 10))
        tabla = ttk.Treeview(marco, columns=("periodo", "ingresos", "gastos", "balance", "estado"), show="headings", height=11)
        for clave, texto, ancho in (("periodo", "Período", 180), ("ingresos", "Ingresos", 150), ("gastos", "Gastos", 150), ("balance", "Balance", 150), ("estado", "Estado", 120)):
            tabla.heading(clave, text=texto)
            tabla.column(clave, width=ancho, anchor="e" if clave in {"ingresos", "gastos", "balance"} else "w")
        reportes = {reporte["periodo"]: reporte for reporte in listar_reportes()}
        reportes[self.periodo] = resumen_mensual(self.periodo)
        for periodo, reporte in sorted(reportes.items(), reverse=True):
            estado = "Mes activo" if periodo == self.periodo else "Cerrado"
            tabla.insert("", "end", iid=periodo, values=(etiqueta_periodo(periodo), moneda(reporte["ingresos"]), moneda(reporte["gastos"]), moneda(reporte["balance"]), estado))
        tabla.pack(fill="both", expand=True, padx=12, pady=12)
        botones = ctk.CTkFrame(self.contenido, fg_color="transparent")
        botones.pack(fill="x", padx=35, pady=(0, 24))
        def periodo_seleccionado():
            seleccionado = tabla.selection()
            if not seleccionado:
                messagebox.showinfo("Selecciona un reporte", "Selecciona un mes de la lista.", parent=self)
                return None
            return seleccionado[0]
        def descargar_mes_csv():
            periodo = periodo_seleccionado()
            if not periodo:
                return
            destino = Path(__file__).resolve().parent / "reports" / f"reporte_{periodo}.csv"
            exportar_reporte_mensual(destino, periodo)
            messagebox.showinfo("Reporte mensual", f"Archivo creado:\n{destino}", parent=self)
        def descargar_mes_pdf():
            periodo = periodo_seleccionado()
            if not periodo:
                return
            try:
                destino = Path(__file__).resolve().parent / "reports" / f"reporte_{periodo}.pdf"
                exportar_reporte_mensual_pdf(destino, periodo)
                messagebox.showinfo("Reporte mensual", f"Archivo creado:\n{destino}", parent=self)
            except ImportError:
                messagebox.showerror("Falta una dependencia", "Instala las dependencias con: py -m pip install -r requirements.txt", parent=self)
        ctk.CTkButton(botones, text="Descargar PDF", command=descargar_mes_pdf, width=170).pack(side="right")
        ctk.CTkButton(botones, text="Descargar CSV", command=descargar_mes_csv, width=170).pack(side="right", padx=10)
        def cerrar_mes():
            cerrar_mes_actual()
            messagebox.showinfo("Reporte actualizado", "El reporte del período actual fue generado. El mes se cerrará automáticamente al cambiar el calendario.", parent=self)
            self.mostrar_reportes()
        ctk.CTkButton(botones, text="Generar reporte del mes activo", command=cerrar_mes, width=250).pack(side="right", padx=10)


if __name__ == "__main__":
    SistemaContabilidad().mainloop()
