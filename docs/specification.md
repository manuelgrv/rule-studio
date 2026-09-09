# Especificación del producto

La demo se construirá localmente, con herramientas independientes de Databricks y datos bancarios sintéticos. El destino es Databricks Apps, Lakebase, lakehouse edv/prod y biblioteca publicada en Artifactory. La plataforma destino existe pero no es dependencia para ejecutar la demo.

## Tres módulos

1. **Selección de inputs:** catálogo de fuentes existentes, campos tipados, uniones encadenadas y estructura por cliente. Genera el DSL de consolidación. Arrays de objetos para 1:N; cero coincidencias genera [].
2. **Variables virtuales:** aritmética y variables encadenadas del mismo cliente, catálogo y traza. Operaciones sobre arrays: suma, conteo, mínimo, máximo, promedio, existe y todos. Estadísticas complejas fuera del MVP.
3. **Estudio de reglas:** autoría low-code, Python restringido y SQL sin bibliotecas de usuario. Reglas booleanas, productos con AND/OR/NOT, paquete de evaluación con dependencias fijadas.

## UI y permisos

Dashboard SPA React/TypeScript/Vite con shadcn/ui y backend FastAPI. Permisos para crear inputs, variables y reglas, y aprobar cada tipo; no se deducen de títulos como PO o Risk Specialist. Ediciones personales privadas; catálogo de versiones publicadas con acceso autorizado. Sin autoaprobación.

Experimentación → propuesto → publicado. Rechazado vuelve a experimentación conservando historial. Publicación automática después de aprobación válida; una definición de input vigente y una evaluación vigente por producto. El paquete completo requiere un permiso específico de aprobación, independiente de la autoría.

La UI usa la biblioteca compartida mediante backend para compilar entradas visuales, Python y SQL. Ofrece diagnósticos, visualización y descarga de los dos JSON. Su flujo termina al publicar el DSL; no controla ejecuciones productivas. Descarga a workspace remoto queda para otra etapa.

## Ejecución y resultados

Notebook local consume los mismos paquetes y la misma biblioteca, materializa input y ejecuta evaluación. Tres salidas: cliente/producto/ejecución; variables por cliente/ejecución; reglas/resultados por cliente/ejecución. Las dos trazas contienen colecciones tipadas.

Cada regla válida retorna booleano. Fallos en ejecución se persisten como null con error técnico en reglas y productos afectados; otros productos continúan. Evaluar todas las reglas seleccionadas. No existen excepciones individuales ni revisión manual como resultado de negocio.

Input compartido, clave (execution_id, date, client, version), partición execution_id, fecha de procesamiento y versión de definición. Seleccionar materialización completada explícitamente; reintentos fijan el mismo input e ID.

## Entregables y aceptación

UI local funcional; biblioteca Python empaquetable; notebook ejecutable; tests sintéticos; dos especificaciones DSL formales. Demo de 30 mil clientes reproducibles; objetivo futuro de 30 millones requiere medición independiente.

Los tests demostrarán paridad de autorías, tipos y nulabilidad, arrays y cardinalidades, trazabilidad, continuidad ante error de regla/producto, publicación y permisos. La demo debe funcionar sin credenciales ni conexiones a los servicios del banco.

Ver [plan de demo](synthetic-mvp.md), [DSL](dsl/README.md) y [acuerdos de cierre](cierre-de-diseno.md).
