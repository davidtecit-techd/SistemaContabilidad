# Sistema de Contabilidad

Aplicación de escritorio para registrar ingresos y gastos de un negocio.

## Funciones

- Registro de ingresos y gastos por mes, usando la fecha del equipo.
- Resumen mensual: ingresos, gastos, balance y meta diaria.
- Edición de movimientos sin borrarlos.
- Categorías de gastos personalizables.
- Gastos mensuales recurrentes que se registran una sola vez por período.
- Inventario editable con cantidad, costo unitario y valor total disponible.
- Reportes mensuales y globales descargables en CSV o PDF.
- Copia de seguridad automática de la base de datos cada siete días.
- Almacenamiento local mediante SQLite, sin conexión a Internet.

## Ejecución

Instala la dependencia y ejecuta la aplicación:

```bash
py -m pip install -r requirements.txt
py main.py
```

Si el comando `py` indica que no hay una versión de Python instalada, instala
Python 3 desde https://www.python.org/downloads/ y marca la opción para añadir
Python al PATH durante la instalación.

La base de datos se crea automáticamente en `database/sistema.db`.
