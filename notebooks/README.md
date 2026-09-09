# Notebooks de demo

Ejecutar en orden 01 → 02 → 03 desde la raíz del proyecto:

```sh
uv sync --extra dev
uv run python scripts/run_notebooks.py
```

El script usa el Python del proyecto, crea un kernel temporal y guarda los resultados en cada notebook. No instala kernels globales.

- 01: genera/verifica 30 mil clientes en data/banking.duckdb, materializa STRUCT/LIST y exporta Parquet particionado.
- 02: compara autoría visual/Python/SQL, muestra diagnósticos y exporta los ejemplos JSON completos.
- 03: genera 90 mil evaluaciones, las dos trazas y comprueba continuidad por producto e idempotencia.

Usan datos ficticios exclusivamente y la biblioteca compartida. Repetirlos conserva la ejecución existente si la definición no cambia. Para un experimento con otra lógica, usar un execution_id nuevo; no sobrescribir la ejecución de referencia.
