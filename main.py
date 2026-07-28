import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class SistemaContabilidad(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Sistema de Contabilidad")
        self.geometry("1200x700")

        self.crear_dashboard()

    def crear_dashboard(self):

        titulo = ctk.CTkLabel(
            self,
            text="Sistema de Contabilidad",
            font=("Segoe UI", 28, "bold")
        )

        titulo.pack(pady=20)

        self.ingresos = ctk.CTkFrame(self, width=250, height=120)
        self.ingresos.pack(pady=10)

        ctk.CTkLabel(
            self.ingresos,
            text="Ingresos del Mes",
            font=("Segoe UI", 18)
        ).pack(pady=10)

        self.lbl_ingresos = ctk.CTkLabel(
            self.ingresos,
            text="₡0",
            font=("Segoe UI", 24, "bold")
        )

        self.lbl_ingresos.pack()

        self.gastos = ctk.CTkFrame(self, width=250, height=120)
        self.gastos.pack(pady=10)

        ctk.CTkLabel(
            self.gastos,
            text="Gastos Mensuales",
            font=("Segoe UI", 18)
        ).pack(pady=10)

        self.lbl_gastos = ctk.CTkLabel(
            self.gastos,
            text="₡0",
            font=("Segoe UI", 24, "bold")
        )

        self.lbl_gastos.pack()

        self.meta = ctk.CTkFrame(self, width=250, height=120)
        self.meta.pack(pady=10)

        ctk.CTkLabel(
            self.meta,
            text="Meta Diaria",
            font=("Segoe UI", 18)
        ).pack(pady=10)

        self.lbl_meta = ctk.CTkLabel(
            self.meta,
            text="₡0",
            font=("Segoe UI", 24, "bold")
        )

        self.lbl_meta.pack()

        botones = ctk.CTkFrame(self)
        botones.pack(pady=20)

        ctk.CTkButton(
            botones,
            text="Agregar Ingreso",
            width=200
        ).grid(row=0, column=0, padx=10)

        ctk.CTkButton(
            botones,
            text="Agregar Gasto",
            width=200
        ).grid(row=0, column=1, padx=10)

        ctk.CTkButton(
            botones,
            text="Reportes",
            width=200
        ).grid(row=0, column=2, padx=10)


if __name__ == "__main__":
    app = SistemaContabilidad()
    app.mainloop()