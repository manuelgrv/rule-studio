# Entornos, edición y publicación

## Demo local confirmada

UI React/TypeScript/Vite + shadcn/ui; FastAPI consume la misma biblioteca Python que el notebook. Datos sintéticos locales y tests, sin depender de Databricks, Lakebase o Artifactory. Almacenamiento local y adaptadores se concretarán al construir; no simular integración real como si estuviera validada.

## Destino futuro

| Plataforma | Responsabilidad |
| --- | --- |
| Databricks Apps | Autoría, validación, versiones y publicación de DSL |
| Lakebase | Ediciones, permisos, revisiones, espacios personales y metadatos |
| Lakehouse edv | Inputs y ejecuciones experimentales |
| Lakehouse prod | DSL aprobado, input y tres salidas productivas |
| Artifactory | Distribución de la biblioteca versionada |
| Orquestación externa | Programación y operación productiva; Lakeflow Jobs como tecnología objetivo, fuera de la UI |

La infraestructura existe, pero integración y despliegue no pertenecen a la demo local. No se requieren dos apps ni workspaces Databricks distintos.

## Roles y flujo

Permisos separados de creación/aprobación para inputs, variables y reglas, configurables sin depender de cargos organizacionales. No autoaprobación. Ediciones privadas, versiones publicadas compartidas bajo autorización. Publicación por paquete de evaluación y versión de inputs. Aprobar el paquete completo requiere su permiso específico; no se acumulan aprobaciones de variables/reglas.

Experimentación → propuesto → publicado; rechazo vuelve a experimentación con historial. Una definición de input vigente y una evaluación vigente por producto. Activar una definición significa hacerla vigente en el registro, no iniciar un job. La UI acaba en publicación.

## Ejecución fuera de la UI

Notebook local demuestra el consumo del DSL. En destino, orquestadores externos fijan ejecución de input completada, fecha y versiones sin sustituciones silenciosas. Reintento conserva ID; nueva corrida intencional usa otro.

Una regla/producto con error registra resultado null y diagnóstico, mientras continúan los demás productos evaluables. Fallos globales de infraestructura se reflejan en estado de ejecución. Las tres salidas son evaluaciones, variables y reglas/resultados. Programación, reintentos y rollback de jobs no son controles de la UI.

## Exportación al workspace — etapa posterior

Es viable diseñar una acción «Guardar en mi workspace» que escriba desde backend mediante Workspace API, en lugar de descargar al equipo. Requiere identidad, scopes y permisos adecuados para la ruta; no basta escribir un archivo en el filesystem de la App. Pendiente validar la configuración concreta del banco.

Fuentes oficiales consultadas el 2026-09-08: [Workspace API/SDK](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/workspace/workspace.html) y [autorización de Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth). Los enlaces AWS no seleccionan la nube del banco.

La demo mantiene visor y descarga JSON. Integración remota y política de exportación quedan para una siguiente etapa.
