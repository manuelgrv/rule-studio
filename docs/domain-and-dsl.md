# Dominio y responsabilidades DSL

## Contratos confirmados

Dos documentos JSON: input consolidado y paquete de variables/evaluaciones. El segundo incluye variables, constantes, reglas y productos con referencias exactas al esquema de input. Ver [DSL](dsl/README.md).

Input: esquema tipado por nodo, fuentes y uniones. Variables: expresiones del mismo cliente y dependencias. Reglas: funciones/expresiones booleanas. Productos: AND/OR/NOT de reglas; una versión vigente por producto. Son responsabilidades dentro de dos contratos, no cuatro archivos independientes.

## Entidades

Definición/versionado de input; materialización; variable/versionado y linaje; regla/versionado y fuente de autoría; producto y paquete de evaluación; revisión; publicación inmutable; ejecución y resultados; eventos auditables.

Ediciones privadas y versiones publicadas compartidas con permisos. Capacidades de creación/aprobación separadas por inputs, variables y reglas. La evaluación se publica por paquete; aprobación mediante permiso específico del paquete completo.

Una publicación fija contenido, versiones y esquema. Cambios incompatibles de input no se activan con evaluaciones incompatibles. La UI termina en publicación. Los procesos externos y el notebook consumen DSL; no se controlan jobs productivos desde la UI.

## Biblioteca común

Constructores visuales y compiladores Python/SQL → DSL tipada → validación/plan → backend de ejecución. App/FastAPI y notebook usan la misma biblioteca Python. No ejecutar fuente para descubrir tipos. No bibliotecas de usuario en el MVP. Python restringido retorna booleano en todos sus caminos.

Biblioteca empaquetable local, distribuida en Artifactory en integración posterior. Dominio/compilación independientes de SDK Databricks y almacenamiento remoto. Separar adaptadores de plataforma de la lógica.

## Semánticas confirmadas

No excepciones individuales ni overrides. Reglas exitosas true/false; errores de ejecución producen resultado null con diagnóstico e invalidan productos dependientes, continuando otros productos. Las tres salidas conservan versiones e ID de ejecución; todas las reglas seleccionadas se evalúan.

Arrays vacíos: suma/conteo 0; min/max/promedio null; existe false; todos true. 1:N ausente []; 1:1 ausente null solo si el contrato lo permite, multiplicidad inesperada error.

## Desarrollo pendiente

JSON Schema, gramática y tipos/operadores detallados, canonicalización/hash, diagnósticos y fixtures de conformidad. No afirmar que los ejemplos ilustrativos constituyen un compilador o esquema terminado. Ver [cierre](cierre-de-diseno.md).
