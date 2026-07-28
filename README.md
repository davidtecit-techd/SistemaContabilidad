# Sistema de Contabilidad

Aplicación de escritorio para registrar ingresos y gastos de un negocio.

## Funciones

- Registro de ingresos y gastos con fecha, descripción y categoría.
- Resumen mensual: ingresos, gastos, balance y meta diaria.
- Consulta y eliminación de movimientos.
- Exportación de todos los movimientos a CSV.
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
