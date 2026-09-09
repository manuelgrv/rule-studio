# Arquitectura vigente

## Dos ámbitos explícitos

La demo es local e independiente de la plataforma final. El diseño destino utiliza Databricks Apps, Lakebase, lakehouse edv/prod y Artifactory. La UI acaba en publicar DSL; la cadena de consumo hasta las tres tablas se muestra para explicar el contrato, con ejecución productiva controlada externamente.

## Núcleo compartido y adaptadores

React/TypeScript/Vite + shadcn/ui → FastAPI → biblioteca Python. El notebook importa la misma biblioteca. No duplicar semántica entre editor visual, compiladores Python/SQL y notebook.

La biblioteca contiene construcción/validación DSL, traducción de fuentes permitidas y generación/interpretación de planes. Python de autoría se analiza como AST sin ejecutarlo. No admite bibliotecas de usuario; PySpark y otras dependencias internas del backend no están sujetas a esa restricción.

El dominio, los contratos JSON y la lógica del compilador no requieren SDK Databricks ni rutas de catálogos bancarios. Adaptadores de catálogo, persistencia, publicación y ejecución permiten usar fuentes y almacenamiento locales durante la demo. PySpark puede operar localmente; no es necesario un runtime Databricks para demostrar contratos.

## Publicación

Lakebase en destino, almacenamiento local en demo: ediciones privadas, roles y revisiones. Registro de DSL publicado: versiones inmutables con dependencias fijadas, una definición de input vigente y una evaluación vigente por producto. Publicación automática después de aprobación autorizada. Guardar descarga no publica.

La UI no inicia jobs productivos ni administra su programación/reintentos/rollback. No confundir vigencia del DSL con activación de infraestructura. Cambios incompatibles de input no deben activar criterios inconsistentes.

## Consumo y trazabilidad

Notebook o proceso externo → biblioteca → input consolidado y tres salidas. Resultados por cliente/producto/ejecución, variables y reglas por cliente/ejecución. Errores aislables dejan resultados null con diagnósticos en dependencias afectadas sin detener otros productos.

El input conserva execution_id/date/client/version y partición por ejecución. Contrato por nodo, arrays anidados, [] para 1:N ausente. La ejecución fija materialización completada y versiones exactas.

## Distribución y validación futura

Biblioteca empaquetable localmente; publicación en Artifactory para integración posterior. Notebook y UI consumen la misma versión. Instalación durante preparación del entorno, no por cada cliente.

La demo usa 30 mil clientes sintéticos. Capacidad para 30 millones, identidad de producción, red, políticas de exportación, retención y operación externa requieren validación posterior.

Diagramas: [LikeC4](c4/README.md). Acuerdos: [cierre de diseño](cierre-de-diseno.md).
