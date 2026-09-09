# Demo local y pruebas

## Entregables confirmados

- UI SPA React/TypeScript/Vite + shadcn/ui con tres módulos, roles, versiones, revisión/publicación y visor/descarga JSON.
- Backend FastAPI que consume la biblioteca común para construir DSL visual y compilar Python/SQL.
- Biblioteca Python independiente de la plataforma final, empaquetable para posterior Artifactory.
- Notebook local ejecutable que importa esa biblioteca y demuestra consolidación/evaluación.
- Tests automatizados con datos bancarios sintéticos locales y dos esquemas DSL formales.

No requiere acceso a Databricks, Lakebase ni Artifactory, aunque el banco dispone de ellos. La demo no publica datos ni ejecuta decisiones de clientes reales. La UI termina en publicación del DSL; el notebook demuestra su consumo.

## Fixture bancario sintético

30 mil clientes deterministas con semilla fija, cuentas, ingresos, deudas y relaciones familiares. Definir entidades ficticias, uniones encadenadas 1:1/1:N, listas vacías, varios arrays independientes y variables encadenadas. Casos pequeños adicionales para inspección manual.

Resultados de referencia son criterios ficticios, no políticas bancarias. Volumen productivo objetivo de 30 millones se valida después.

## Recorrido del notebook

1. Crear fuentes locales y cargar definición de input construida con la biblioteca.
2. Validar esquema y materializar input por execution_id/date/client/version.
3. Cargar paquete de variables/evaluaciones publicado por la UI o fixture equivalente.
4. Ejecutar con la misma biblioteca y guardar las tres salidas locales.
5. Mostrar traza de un cliente y un producto con fallo, junto a otro producto evaluado correctamente.
6. Demostrar selección explícita de input, versiones fijadas y reintento idempotente.

## Tests de aceptación

- Equivalencia entre low-code, Python restringido y SQL para casos admitidos.
- Rechazo de imports, código no permitido, retorno no booleano, referencias/tipos inválidos y dependencias cíclicas.
- 1:N vacía [], 1:1 ausente según nulabilidad y error por multiplicidad inesperada.
- Arrays independientes de tamaños 2 y 3 conservan tamaños y una fila por cliente.
- Arrays vacíos: suma/conteo 0, min/max/promedio null, existe false, todos true.
- Null explícito en autoría; return None no compila. Error de ejecución produce resultado null con diagnóstico.
- Un producto con regla fallida queda null mientras otro producto conserva su resultado. Evaluar todas las reglas seleccionadas.
- Tres salidas correlacionadas; dependencias/versiones reproducibles.
- Permisos por capacidad, rechazo de autoaprobación, publicación de contenido exacto y una versión vigente por producto.
- JSON visible/descargable desde UI generado por la misma biblioteca que el notebook.

Precisión, tipos físicos, serialización y límites se fijarán con schemas y fixtures antes de implementar cada operador. No hacer pasar una demo sintética por prueba de capacidad productiva.
