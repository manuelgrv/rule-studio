# C4 architecture with LikeC4

[architecture.c4](architecture.c4) is the executable architecture model and source of truth for interactive diagrams. Internal runtime boundaries are proposed; confirmed functional requirements are described in the specification.

From the project root:

```sh
likec4 validate docs/c4
likec4 start docs/c4 --listen 127.0.0.1 --port 5179 --title 'Arquitectura del gestor de reglas'
```

Open [the local preview](http://127.0.0.1:5179). The installed LikeC4 CLI is used; no project dependency installation is required.

[Arquitectura global](http://127.0.0.1:5179/view/global_architecture/) resume las plataformas, la biblioteca y las tablas con las conexiones principales.

Review order:

1. [Contexto del sistema](http://127.0.0.1:5179/view/index/): roles, entrada y salida productiva.
2. [Módulo 1 — Selección de inputs](http://127.0.0.1:5179/view/module_1/): fuentes, uniones, DSL y materialización.
3. [Módulo 2 — Variables virtuales](http://127.0.0.1:5179/view/module_2/): variables autorizadas, expresiones y cálculo.
4. [Módulo 3 — Estudio de reglas](http://127.0.0.1:5179/view/module_3/): reglas, composición lógica de productos, aprobación y tres salidas trazables.
5. [Arquitectura global](http://127.0.0.1:5179/view/global_architecture/): visión conjunta de plataformas y datos.

Las cinco vistas del destino sustituyen las vistas genéricas de contenedores, componentes y procesamiento. En las vistas de módulos, los grupos identifican Databricks Apps, procesamiento Python en Databricks, Databricks Lakehouse y distribución mediante Artifactory. Lakebase conserva las definiciones editables; el lakehouse almacena los planes publicados y las salidas de ejecución. La biblioteca se ejecuta dentro del proceso que la utiliza; su grupo visual no representa un servicio remoto.

The Markdown Mermaid files are earlier planning sketches. Update the LikeC4 model first during architecture review. Container means a runtime or storage boundary, not necessarily a Docker container. The model is logical: cloud-specific deployment and compute selection remain open.

Open review points: completed-input selection, special input approver role, output schemas, and integration of the compiler/interpreter library into its consumers. The scheduler is an explicit proposed component supporting the confirmed scheduled-batch requirement.

## Visual notation

- Warm gray people: user roles.
- Muted slate platform: Databricks-hosted system boundary.
- Dusty blue browser/component shapes: App UI and authoring modules.
- Sage components with Python icons: compilation and execution processes.
- Muted sand components: authorization, validation, review, and orchestration.
- Muted teal cylinders: lakehouse tables.
- Muted mauve storage/document shapes: workflow metadata and versioned execution artifacts.
- Gray rectangles: external systems, when explicitly in scope.

The bundled Databricks logo comes from LikeC4's Azure icon pack; it does not select Azure as the deployment cloud. Frontend framework icons are deferred until the stack is selected.

## Ongoing visual review standard

Keep the global view grouped by responsibility with only the main connections. Collapse App internals into a navigable node; preserve all three modules in its description and component drill-down. Keep routine status, metadata, and authorization dependencies in detailed views. After model changes, validate and visually inspect the rendered overview for crossing edges, readable labels, and useful grouping. Visual groups do not imply new services or deployment boundaries. Retain the muted palette.

Diagram language: Spanish for every visible title, description, group, notation, and relationship. Preserve technology names and technical identifiers. Apply this convention to future diagram changes.
La vista module_3 integra reglas y productos; sustituye module_4. Las salidas son evaluaciones, variables materializadas y reglas/resultados por cliente.

## Alcance de entrega vigente

[Demo local](http://127.0.0.1:5179/view/demo_local/): UI, FastAPI, biblioteca compartida, notebook y datos sintéticos. Las cinco vistas anteriores describen el destino Databricks; la nueva vista separa la entrega local. La UI termina en publicar DSL; orquestación productiva externa. Roles por capacidades, no títulos.
