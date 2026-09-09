# Módulos y alcance vigentes

Esta revisión sustituye los límites antiguos de ejecución en UI. La [especificación](specification.md) y [cierre de diseño](cierre-de-diseno.md) contienen los acuerdos actuales.

## 1. Selección de inputs

Permiso de creación de inputs. Catálogo de fuentes y esquema por nodo, uniones encadenadas, objetos y arrays de objetos. DSL descargable/versionado; aprobación independiente antes de sustituir la única definición productiva vigente. Compartido entre productos.

1:N sin coincidencias produce []; 1:1 ausente produce null solo si está permitido; multiplicidad inesperada es error. La materialización en notebook/proceso externo conserva una fila por cliente dentro de ejecución/fecha/versión.

## 2. Variables virtuales

Permiso de creación de variables. Aritmética del mismo cliente, dependencias acíclicas, catálogo con linaje y operaciones sobre arrays (suma, conteo, mínimo, máximo, promedio, existe/todos). Estadísticas complejas quedan fuera del MVP.

Guardar definición no materializa valores. El notebook/proceso consumidor calcula y guarda una colección de variables tipadas por cliente/ejecución para traza.

## 3. Estudio de reglas

Permiso de creación de reglas. Inputs, variables y constantes alimentan reglas booleanas creadas visualmente o por Python/SQL restringido sin imports/bibliotecas. Los productos solo combinan resultados con lógica booleana.

La descarga de evaluación incluye variables, reglas, productos y versiones exactas de dependencias. Se aprueba el paquete completo con un permiso específico, sin aprobaciones separadas de sus variables/reglas. Una evaluación vigente por producto.

La UI termina en publicación. La misma biblioteca genera DSL desde la UI y permite ejecutarlo desde notebook. No se implementan controles productivos de jobs en la aplicación.

## Tres salidas del consumidor

- Evaluaciones: una fila por cliente/producto/ejecución.
- Variables: una fila por cliente/ejecución con colección tipada y versiones.
- Reglas: una fila por cliente/ejecución con colección de reglas/resultados y versiones.

Reglas válidas retornan true/false. Resultado de ejecución nullable por error técnico; el producto dependiente queda null, continúan los demás. No se cambia el contrato de función Python a Optional[bool].

## Demo y destino

Demo local: React/TypeScript/Vite, shadcn/ui, FastAPI, biblioteca, notebook y tests sobre 30 mil clientes sintéticos. Sin dependencia de la infraestructura bancaria. Destino futuro: Databricks Apps, Lakebase, lakehouse edv/prod y Artifactory. Guardar DSL al workspace remoto es una etapa posterior.
