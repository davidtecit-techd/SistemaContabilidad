from __future__ import annotations

from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk

from database.database import (
    agregar_gasto,
    agregar_ingreso,
    eliminar_movimiento,
    inicializar_base_datos,
    listar_movimientos,
)
from modules.calculadora import resumen_mensual
from modules.reportes import exportar_csv


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def moneda(monto: float) -> str:
    return f"₡{monto:,.2f}"


class SistemaContabilidad(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_base_datos()
        self.title("Sistema de Contabilidad")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._crear_menu()
        self.contenido = ctk.CTkFrame(self, corner_radius=0)
        self.contenido.grid(row=0, column=1, sticky="nsew")
        self.mostrar_dashboard()

    def _crear_menu(self):
        menu = ctk.CTkFrame(self, width=210, corner_radius=0)
        menu.grid(row=0, column=0, sticky="nsew")
        menu.grid_propagate(False)
        ctk.CTkLabel(menu, text="CONTABILIDAD", font=("Segoe UI", 22, "bold")).pack(pady=(35, 4))
        ctk.CTkLabel(menu, text="Control simple de tu negocio", text_color="gray70").pack(pady=(0, 30))
        for texto, comando in [
            ("Inicio", self.mostrar_dashboard),
            ("Nuevo ingreso", lambda: self.abrir_formulario("ingresos")),
            ("Nuevo gasto", lambda: self.abrir_formulario("gastos")),
            ("Movimientos", self.mostrar_movimientos),
            ("Reportes", self.mostrar_reportes),
        ]:
            ctk.CTkButton(menu, text=texto, command=comando, width=170, height=38).pack(pady=6)

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def mostrar_dashboard(self):
        self.limpiar_contenido()
        resumen = resumen_mensual()
        ctk.CTkLabel(self.contenido, text="Resumen del mes", font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=35, pady=(30, 6))
        ctk.CTkLabel(self.contenido, text=f"Actualizado al {date.today():%d/%m/%Y}", text_color="gray70").pack(anchor="w", padx=35, pady=(0, 22))
        tarjetas = ctk.CTkFrame(self.contenido, fg_color="transparent")
        tarjetas.pack(fill="x", padx=30)
        tarjetas.grid_columnconfigure((0, 1, 2, 3), weight=1)
        datos = [("Ingresos", resumen["ingresos"], "#1f9d55"), ("Gastos", resumen["gastos"], "#e05252"), ("Balance", resumen["balance"], "#3584e4"), ("Meta diaria", resumen["meta_diaria"], "#a56de2")]
        for columna, (titulo, valor, color) in enumerate(datos):
            tarjeta = ctk.CTkFrame(tarjetas, border_width=1, border_color=color)
            tarjeta.grid(row=0, column=columna, padx=7, sticky="ew")
            ctk.CTkLabel(tarjeta, text=titulo, font=("Segoe UI", 15)).pack(pady=(18, 4))
            ctk.CTkLabel(tarjeta, text=moneda(float(valor)), font=("Segoe UI", 21, "bold"), text_color=color).pack(pady=(0, 18))
        ctk.CTkLabel(self.contenido, text="Últimos movimientos", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=35, pady=(36, 10))
        self._tabla_movimientos(self.contenido, limite=8)

    def _tabla_movimientos(self, padre, limite=None):
        marco = ctk.CTkFrame(padre)
        marco.pack(fill="both", expand=True, padx=35, pady=(0, 25))
        tabla = ttk.Treeview(marco, columns=("tipo", "fecha", "descripcion", "categoria", "monto"), show="headings", height=10)
        for clave, texto, ancho in [("tipo", "Tipo", 90), ("fecha", "Fecha", 100), ("descripcion", "Descripción", 280), ("categoria", "Categoría", 150), ("monto", "Monto", 130)]:
            tabla.heading(clave, text=texto)
            tabla.column(clave, width=ancho, anchor="e" if clave == "monto" else "w")
        filas = []
        for tipo in ("ingresos", "gastos"):
            for movimiento in listar_movimientos(tipo, limite):
                filas.append((movimiento["fecha"], tipo, movimiento))
        for _, tipo, movimiento in sorted(filas, key=lambda fila: (fila[0], fila[2]["id"]), reverse=True)[:limite]:
            tabla.insert("", "end", iid=f"{tipo}:{movimiento['id']}", values=(tipo[:-1].title(), movimiento["fecha"], movimiento["descripcion"], movimiento["categoria"] if tipo == "gastos" else "—", moneda(movimiento["monto"])))
        tabla.pack(fill="both", expand=True, padx=12, pady=12)
        return tabla

    def abrir_formulario(self, tipo):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Nuevo ingreso" if tipo == "ingresos" else "Nuevo gasto")
        ventana.geometry("420x360" if tipo == "gastos" else "420x300")
        ventana.transient(self)
        ventana.grab_set()
        ctk.CTkLabel(ventana, text="Registrar " + ("ingreso" if tipo == "ingresos" else "gasto"), font=("Segoe UI", 22, "bold")).pack(pady=(25, 18))
        campos = {}
        for clave, etiqueta, ejemplo in [("monto", "Monto", "Ejemplo: 25000"), ("descripcion", "Descripción", "Ejemplo: Venta del día"), ("fecha", "Fecha", "AAAA-MM-DD")]:
            ctk.CTkLabel(ventana, text=etiqueta).pack(anchor="w", padx=45)
            entrada = ctk.CTkEntry(ventana, placeholder_text=ejemplo, width=330)
            entrada.pack(pady=(2, 9))
            campos[clave] = entrada
        campos["fecha"].insert(0, date.today().isoformat())
        if tipo == "gastos":
            ctk.CTkLabel(ventana, text="Categoría").pack(anchor="w", padx=45)
            campos["categoria"] = ctk.CTkEntry(ventana, placeholder_text="Ejemplo: Alquiler", width=330)
            campos["categoria"].pack(pady=(2, 12))

        def guardar():
            try:
                if tipo == "ingresos":
                    agregar_ingreso(campos["monto"].get(), campos["descripcion"].get(), campos["fecha"].get())
                else:
                    agregar_gasto(campos["monto"].get(), campos["descripcion"].get(), campos["categoria"].get(), campos["fecha"].get())
            except ValueError as error:
                messagebox.showerror("Datos no válidos", str(error), parent=ventana)
                return
            ventana.destroy()
            self.mostrar_dashboard()

        ctk.CTkButton(ventana, text="Guardar", command=guardar, width=180).pack(pady=14)

    def mostrar_movimientos(self):
        self.limpiar_contenido()
        ctk.CTkLabel(self.contenido, text="Movimientos", font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=35, pady=(30, 16))
        tabla = self._tabla_movimientos(self.contenido)
        def borrar():
            seleccionado = tabla.selection()
            if not seleccionado:
                messagebox.showinfo("Selecciona un movimiento", "Selecciona una fila para eliminarla.", parent=self)
                return
            tipo, movimiento_id = seleccionado[0].split(":")
            if messagebox.askyesno("Eliminar movimiento", "¿Deseas eliminar este movimiento?", parent=self):
                eliminar_movimiento(tipo, int(movimiento_id))
                self.mostrar_movimientos()
        ctk.CTkButton(self.contenido, text="Eliminar movimiento seleccionado", fg_color="#b54545", hover_color="#8f3434", command=borrar).pack(anchor="e", padx=35, pady=(0, 25))

    def mostrar_reportes(self):
        self.limpiar_contenido()
        resumen = resumen_mensual()
        ctk.CTkLabel(self.contenido, text="Reporte mensual", font=("Segoe UI", 28, "bold")).pack(anchor="w", padx=35, pady=(30, 20))
        texto = (f"Ingresos del mes:  {moneda(resumen['ingresos'])}\n\nGastos del mes:     {moneda(resumen['gastos'])}\n\nBalance neto:       {moneda(resumen['balance'])}\n\nMeta diaria:        {moneda(resumen['meta_diaria'])}")
        ctk.CTkLabel(self.contenido, text=texto, justify="left", font=("Segoe UI", 18)).pack(anchor="w", padx=45, pady=15)
        def exportar():
            destino = Path(__file__).resolve().parent / "reports" / f"movimientos_{date.today():%Y_%m_%d}.csv"
            exportar_csv(destino)
            messagebox.showinfo("Reporte exportado", f"Se creó el archivo:\n{destino}", parent=self)
        ctk.CTkButton(self.contenido, text="Exportar todos los movimientos a CSV", command=exportar, width=300).pack(anchor="w", padx=45, pady=25)


if __name__ == "__main__":
    SistemaContabilidad().mainloop()
