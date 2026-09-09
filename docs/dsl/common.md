# Contrato común — propuesta v0.1

Referencia implementada: [DSL v0.1](v0.1.md), esquemas y ejemplos ejecutados. Las propuestas/fragmentos anteriores que siguen se conservan como contexto de diseño; v0.1 define la sintaxis efectiva.
## Identidad y versiones

Cada documento declara kind, dsl_version, definition_id, definition_version, created_by y created_at. La versión del lenguaje es distinta de la versión de definición.

Las referencias publicadas fijan versiones exactas, nunca «latest». Lakebase conserva ediciones por usuario, fuente de autoría y revisiones. Descargar no publica ni concede permisos. La aprobación vincula contenido y dependencias; modificar cualquiera exige nueva revisión. Solo una definición de input está vigente en producción, conservando su historia.

Propuesta: registrar hash del contenido, versión de biblioteca/compilador y evidencia de aprobación en un manifiesto de publicación. La canonicalización para hashes queda pendiente.

## Contrato tipado

Tipos propuestos: boolean, integer, decimal con precisión/escala, string, date, timestamp, struct y array. Declarar nulabilidad de campos y elementos. Cada referencia se verifica contra el esquema de input fijado y las variables incluidas.

Validar estructura, nombres, tipos, cardinalidades, ciclos y firmas de operadores. Una regla válida produce booleano no nulo. En ejecución, un fallo se registra como resultado null con diagnóstico para regla/producto afectados; no se convierte en Denegado. El esquema de resultados debe permitir null por error, aunque la expresión de autoría no pueda retornarlo.

Confirmado: ausencia 1:N produce []; 1:1 ausente admite null solo si el esquema lo permite, y multiplicidad inesperada causa error. Arrays vacíos: suma/conteo=0, min/max/promedio=null, existe=false, todos=true. Null exige tratamiento explícito en reglas. Pendiente de implementación: redondeo, overflow, división por cero, zonas horarias, elementos null de arrays y control de flujo acotado. No adoptar accidentalmente las diferencias entre Python, pandas y Spark.

## Manifiesto de ejecución separado

La lógica no contiene datos cambiantes de cada lote. El manifiesto identifica entorno edv/prod, release/hash, fecha de procesamiento, execution_id, materialización de input y versión de biblioteca. Distinguir la ejecución del input de la evaluación y enlazarlas.

Los destinos físicos se resuelven desde configuración autorizada; escribir una tabla en JSON no concede acceso. La partición execution_id no garantiza idempotencia por sí sola: los reintentos necesitan una política propia.

## Diagnósticos y conformidad

Errores con código, ruta JSON y línea/columna de Python cuando corresponda: UNKNOWN_FIELD, TYPE_MISMATCH, CYCLIC_DEPENDENCY, UNSUPPORTED_SYNTAX y NON_BOOLEAN_RETURN.

JSON Schema valida estructura; un validador semántico comprueba referencias, tipos y ciclos. Verificar también el esquema real al ejecutar. Crear casos válidos e inválidos y pruebas de equivalencia entre low-code, Python/SQL, interpretación y ejecución distribuida.

Confirmado: el esquema de input declara tipos en todos los niveles, incluidos arrays de objetos anidados. Una relación 1:N sin coincidencias produce `[]`. Las semánticas de arrays vacíos se especifican arriba. Véase [inputs](inputs.md).
