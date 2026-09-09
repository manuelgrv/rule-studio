# Cierre de diseño — acuerdos vigentes

Estado: alcance acordado; permiso específico de aprobación del paquete confirmado. Biblioteca y notebooks locales implementados; UI/workflow e integraciones son etapas posteriores.

## Acuerdos de cierre

| ID | Decisión |
| --- | --- |
| C01 | Roles configurables para crear inputs, variables y reglas; permisos de aprobación para cada tipo, independientes de títulos organizacionales. Sin autoaprobación. |
| C02 | Publicación de evaluación como paquete con variables, reglas, productos y versiones fijadas. |
| C03 | Una definición de input vigente y una evaluación vigente por producto. No activar versiones incompatibles ni migrar criterios silenciosamente. |
| C04 | Aritmética y suma/conteo/mínimo/máximo/promedio sobre arrays del mismo cliente; condiciones existe/todos. Estadísticas complejas después. |
| C05 | Low-code, Python restringido y SQL desde el MVP, sin bibliotecas en código de usuario. El backend interno puede usar sus propias dependencias. |
| C06 | Error de ejecución: resultado null para regla/producto afectados, con diagnóstico técnico. Continuar otros productos y clientes que se puedan evaluar. No convertir errores en Denegado. |
| C07 | 1:N sin coincidencias: []; 1:1 sin coincidencia: null solo si el esquema lo permite; multiplicidad inesperada: error. Array vacío: suma/conteo=0; min/max/promedio=null; existe=false; todos=true. |
| C08 | Evaluaciones por cliente/producto/ejecución; reglas y variables en sus respectivas tablas por cliente/ejecución con colecciones tipadas. Evaluar todas las reglas seleccionadas para trazabilidad. |
| C09 | Input completado explícito para experimentos; ejecución por lotes fija fecha/versión sin sustitución silenciosa de fecha. Reintento conserva ID; nueva ejecución intencional usa otro. |
| C10 | Ediciones privadas, versiones publicadas compartidas con autorización; sin importación de DSL ni edición colaborativa simultánea inicialmente. Guardado al workspace remoto se difiere. |
| C11 | React/TypeScript/Vite + shadcn/ui, FastAPI y biblioteca Python; PySpark como backend de procesamiento. Demo completamente local y con datos sintéticos, sin dependencia de acceso a Databricks/Lakebase/Artifactory. Esas plataformas existen como destino futuro. |
| C12 | La UI termina en publicación del DSL de input o evaluación. Orquestación/ejecución productiva externas; no implementar controles de lotes productivos, activación de jobs ni rollback operativo en la UI. |

## Entregables de demo

1. UI operativa local con tres módulos, permisos, versiones, revisión/publicación, visor y descarga JSON.
2. Biblioteca común usada desde FastAPI para generar/validar DSL visual, Python y SQL; el navegador no mantiene un compilador independiente.
3. Notebook local que usa la misma biblioteca para materializar inputs sintéticos y producir las tres salidas.
4. Tests automatizados con datos sintéticos de banca: compilación, equivalencia, arrays, errores parciales, versiones y permisos.
5. Dos especificaciones JSON con esquemas formales y ejemplos implementados.

La UI hace autoría/validación/publicación. La demostración de ejecución se realiza en notebook; las propuestas antiguas de lanzar lotes desde UI se retiran. La selección/comparación de experimentos puede mostrarse en notebook sin convertirla en orquestación productiva.

## Aprobación del paquete — confirmado

La aprobación de una evaluación completa usa un permiso específico de paquete; no exige acumular aprobaciones separadas de variables y reglas. Se mantiene independencia respecto del autor/solicitante. La implementación del workflow/UI es posterior a la biblioteca actual.

## Semántica de fallo

El contrato de autoría es función booleana: return None no compila. El resultado persistido es nullable por fallos de ejecución, acompañado de estado y error. Una regla fallida invalida los productos que la utilizan para ese cliente; reglas compartidas válidas se conservan. No usar OR true ni AND false para ocultar errores de dependencias. Un fallo global de infraestructura impide completar las salidas; la continuidad por producto no promete recuperarse de almacenamiento indisponible.

## Implementación pendiente, sin reabrir decisiones de producto

Diseñar JSON Schema, gramática SQL/Python acotada, precisión/escala y casts, manejo de elementos null en arrays no vacíos, límites y orden estable, almacenamiento local, migraciones/hash, claves físicas y pruebas. Publicar esos contratos antes de implementar cada operación. La sintaxis actual es ilustrativa; no declarar que ya existe un compilador.

## Integración y producción posteriores

Adaptadores Databricks Apps/Lakebase/lakehouse, distribución en Artifactory, guardar DSL en workspace remoto, identidades/red y pruebas distribuidas. Los 30 mil clientes de demo no prueban capacidad para 30 millones; latencia, concurrencia, retención y recuperación se validarán antes de producción.
