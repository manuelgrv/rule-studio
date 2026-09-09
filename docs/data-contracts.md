# Contratos de datos

Nombres físicos propuestos; granularidades y comportamientos confirmados.

## Input consolidado

Clave lógica (execution_id, date, client, version); partición execution_id. date es fecha de procesamiento; version corresponde a definición. Metadata de creador y procedencia separada de autorización. Input compartido entre productos.

Payload tipado por nodo, objetos y arrays anidados. Una fila por cliente dentro de ejecución/fecha/versión. Cada relación 1:N se consolida antes de combinar otras, evitando multiplicar filas.

1:N sin coincidencias → []; 1:1 ausente → null si se permite; multiplicidad inesperada → error. No fabricar [null] ni elegir una coincidencia arbitraria. Orden estable, límites y duplicados de fuentes son detalles a definir en la implementación.

## Versiones y ejecuciones

Una definición de input vigente. Materializaciones históricas conservan identidad. Input seleccionado debe estar completado y tener versión compatible. Notebook/experimentos seleccionan explícitamente; lotes externos fijan fecha y versión sin recurrir silenciosamente a otra fecha.

Reintento usa el mismo ID e input fijado; una ejecución intencional nueva usa otro. Partición por ID no reemplaza escritura idempotente y validación de unicidad.

La evaluación tiene su propio ID, enlazado al ID de materialización y versiones exactas. Registrar fuente/snapshots disponibles, creador, solicitante e identidad ejecutora con significados separados. Nombres finales de metadata se fijan durante implementación.

## Variables virtuales

Aritmética y dependencias acíclicas por cliente; suma/conteo/mínimo/máximo/promedio y existe/todos sobre arrays. Semántica de vacíos: 0 para suma/conteo, null para min/max/promedio, false para existe y true para todos. La política sobre elementos null dentro de arrays no vacíos debe concretarse en el contrato de operadores.

## Tres salidas

| Tabla | Granularidad confirmada | Contenido |
| --- | --- | --- |
| Evaluaciones | Cliente/producto/ejecución | Resultado booleano nullable, estado técnico, versión de producto/paquete e input y detalles |
| Variables materializadas | Cliente/ejecución | Colección de variables tipadas con ID, versión, valor y traza |
| Reglas/resultados | Cliente/ejecución | Colección de reglas, versiones, resultados booleanos nullable y errores |

IDs de ejecución y versiones correlacionan las tres tablas. Una regla compartida puede referenciar varios productos; no confundir versiones distintas de una regla. Evaluar todas las reglas seleccionadas para traza, aunque AND/OR pudiera cortocircuitar.

## Fallos aislables

Regla fallida → resultado null + error técnico. Producto que la utiliza → resultado null + referencia a la causa; otros productos continúan. Una variable fallida invalida sus dependencias, no las independientes. No confundir valor null permitido con error: el estado/diagnóstico los distingue.

La autoría de regla sigue exigiendo booleano no nulo. Null aparece en el resultado persistido por un fallo, no como tercer resultado de negocio ni como return None admitido.

Fallo de infraestructura global se refleja en el estado de ejecución; no prometer tres salidas completas si no pudieron escribirse. Formato de estado, atomicidad y recuperación se implementan y prueban con las políticas acordadas.

## Demo y destino

Demo: tablas/datasets locales y notebook, almacenamiento físico por concretar. Destino: salidas de experimentos en edv y productivas en prod. La UI publica DSL; los procesos productivos son controlados externamente. Retención y rendimiento productivos se validan después.
