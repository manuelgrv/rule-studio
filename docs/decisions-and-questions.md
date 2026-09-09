> Registro histórico: los acuerdos de [cierre de diseño](cierre-de-diseno.md) sustituyen roles por título, whitelist PySpark/pandas, UI operadora de lotes y pendientes ya resueltos.

# Decisions and discovery backlog

## Confirmed from the initial brief

| ID | Decision |
| --- | --- |
| D-001 | Plan the project in `docs`, with C4 files in `docs/c4`. |
| D-002 | Host the UI in a Databricks App. |
| D-003 | Initially three modules; superseded by D-013 adding a Transformed Field Builder. |
| D-004 | Support low-code and Python/SQL rule authoring using declared datasets. |
| D-005 | Publish product criteria as DSL in a lakehouse table and compile for lakehouse execution. |
| D-006 | Provide analyst experimentation before publication. |

## First discussion — answered 2026-09-05

| ID | Question | Why it matters |
| --- | --- | --- |
| Q-001 | Scheduled production batches and on-demand experiments. | No real-time serving in release one. |
| Q-002 | Final approval decisions. | Results are authoritative business decisions; experiment outputs do not activate production decisions. |
| Q-003 | Analysts experiment and request publication; a separate person approves through a chain, possibly the PO. | No self-approval. Follow-up confirms one approver and automatic publication. |

## Follow-up decisions — confirmed 2026-09-05

| ID | Decision |
| --- | --- |
| D-007 | Use synthetic data for the MVP; real product policies are not required from the user. |
| D-008 | Deliver the Databricks App, rule engines, compilers, interpreters, and DSL language specification. |
| D-009 | Business exceptions are ordinary rules combined through configurable product composition; no individual exceptions or manual overrides. |
| D-010 | One separate person approves a publication request; publication then happens automatically. |
| D-011 | Support moderate complexity in low-code and Python/SQL-to-DSL authoring. Nested groups remain proposed; the earlier scoring/ordered-product interpretation was superseded by D-041 (logical composition only). |

## Latest decisions

D-012 — Module 1 exposes existing lakehouse fields. The earlier deferral of consolidation and transformation ownership is superseded by the following decisions.

| ID | Decision |
| --- | --- |
| D-013 | Historical four-module split; superseded by D-041: products belong inside Module 3. |
| D-014 | Same-client arithmetic and chained variables. Earlier aggregation scope is pending reconfirmation under D-041. |
| D-015 | Module 1 emits retrieval/consolidation DSL for a single input table keyed by date/client/version (extended by D-022 with execution ID), with creator ID metadata and semistructured fields. |
| D-016 | Support chained joins: one-to-one yields scalar/struct, one-to-many yields lists of structs. |
| D-017 | A dedicated role configures Module 1. |
| D-018 | Use Python for processing. Evaluate React/Next.js/Node/Vite frontend options separately. |
| D-019 | High scalability required; store product rule-set execution results in a single lakehouse table. |
| D-020 | Input `version` identifies the dataset definition version. |
| D-021 | Replace author role with creator ID metadata; additional traceability metadata is proposed. |

D-022 — Confirmed: add dataset execution ID to distinguish same-day materializations and partition the input table by that ID. Input key becomes `(execution_id, date, client, version)`. Proposed retry semantics reuse the same execution ID and write idempotently.

D-023 — Confirmed: the compiler and interpreter form a Python library published in Artifactory. This supersedes the proposed standalone compiler worker. Package version pinning and installation during deployment are proposed operational details.

D-024 — Confirmed: scope starts at Module 1 and ends at the lakehouse results table. Remove the speculative external bank consumer from every architecture view.

D-025 — Confirmed: show the production results table explicitly as the system output, with results per client/product plus evaluation details.

D-026 — Confirmed role names: Risk Policy configures Module 1 data; Risk Specialist authors rules and product evaluations, experiments, and requests publication. This naming change does not assign either role as the publication approver.

## Decisiones consolidadas — 2026-09-08

Las respuestas más recientes sustituyen propuestas anteriores incompatibles. Detalle: [entornos y operación](entornos-y-operacion.md).

| ID | Decisión |
| --- | --- |
| D-027 | Product Owner aprueba; catálogo experimental `edv` y productivo `prod`. |
| D-028 | Input compartido; `date` es fecha de procesamiento. |
| D-029 | Catálogo y estructura disponibles para construir DSL; inconsistencias lógicas causan error de compilación. |
| D-030 | Módulo 1 configura la forma semiestructurada. |
| D-031 | Variables derivadas encadenadas y catálogo con traza. |
| D-032 | Persistir variables calculadas en tabla aparte al finalizar evaluación. |
| D-033 | Reglas booleanas: Aceptado/Denegado. |
| D-034 | JSON confirmed; earlier three-document proposal superseded by two agreed contracts in docs/dsl. |
| D-035 | Solo PySpark/pandas en código de usuario; otras bibliotecas no compilan. |
| D-036 | Intérprete modular para construir DSL desde módulos 1, 2 y 3. |
| D-037 | Edición recuperable en Lakebase, acceso por roles y espacios personales. |
| D-038 | Experimentación, propuesto, publicado y rechazado con retorno a experimentación. |
| D-039 | Ejecuciones aprobadas y traza en prod; experimentos en edv. |
| D-040 | Objetivo 30 millones de clientes; demo 30 mil sintéticos. |

Pendientes prioritarios: autor del módulo 2, experiencia del catálogo de variables, esquema de resultados y traza, implementación del espacio personal y selección final del stack. Semántica detallada y operación se revisarán con código por indicación del usuario.

D-041 — Tres módulos vigentes: inputs, variables virtuales y estudio de reglas con composición de productos exclusivamente lógica. DSL descargable y versiones personales; una única definición productiva de input aprobada. Tres tablas de salida y dashboard SPA shadcn/ui. [Detalle y ambigüedades](modulos-vigentes.md).

## Preguntas anteriores — historial, contrastar con D-027 a D-040

- Define which successfully completed input execution a scheduled evaluation selects; pin that ID for reproducibility.
- Proposed creator attribution is the author of the dataset definition version; track job execution identity separately.
- Historical as-of date proposal withdrawn: date is input processing date (D-028). Collection aggregations remain pending.

“Language semantics” means behavior for missing inputs, competing branches, arithmetic errors, and similar cases. “Databricks environment” means cloud provider, workspace setup, and available compute; deployment details remain open and do not block this specification work.

## Subsequent discovery

| ID | Question | Why it matters |
| --- | --- | --- |
| Q-004 | Resolved: use fictional products and synthetic evaluation flows. | No real banking policy required. |
| Q-005 | Input grain confirmed as execution/date/client/definition-version; what population size and collection sizes? | Keys, joins, and capacity |
| Q-006 | Cloud, environments, Unity Catalog setup, and permitted compute? | Deployment feasibility |
| Q-007 | Dedicated role configures sources and chained joins; Module 2 owns transformed fields. Exact permissions remain open. | Module boundary and permissions |
| Q-008 | What exact null/error and Boolean composition semantics should apply? Scoring is excluded. | DSL semantics |
| Q-009 | Who writes Python/SQL and which supported syntax/functions are needed? | Runtime and code governance |
| Q-010 | Historical backtesting, point-in-time data, and comparison metrics required? | Experiment design and retention |
| Q-011 | Closed: scope ends at the results table; external consumers and integrations are excluded. | Confirmed scope boundary |
| Q-012 | Freshness, latency, throughput, availability, and recovery targets? | Nonfunctional requirements |
| Q-013 | Audit retention, explanation requirements, sensitive-data policy, and applicable bank controls? | Governance acceptance criteria |
| Q-014 | Input shared across products is confirmed; parameter and dependency-change policies remain pending. | Reuse and compatibility |
| Q-015 | Scheduling, effective dates, rollback, and operational ownership? | Operational lifecycle |
| Q-016 | Python processing confirmed; SPA/shadcn and Lakebase are confirmed; detailed framework selection remains open. | Implementation choices |

## Proposals to resolve

P-001: immutable versions and pinned dependencies. P-002: distinguish publication from activation. P-003: shared compilation semantics for experiments and production. P-004: distinct authoring/workflow storage boundary. P-005: explicit error states that cannot silently grant approval.

Record future decisions with their answer, date, rationale, and affected files. Unanswered questions must remain visible rather than turning into implicit requirements.

## Decisión — arrays de inputs (2026-09-08)

Confirmado: esquema tipado por nodo, objetos y arrays anidados para relaciones 1:N; ausencia de coincidencias produce `[]`. Mantener una fila por cliente dentro de ejecución/fecha/versión y evitar multiplicación al combinar relaciones. Ver [contrato DSL](dsl/inputs.md). Operadores sobre arrays vacíos, orden y límites siguen pendientes.

## Cierre posterior — confirmado

Roles por capacidades de creación/aprobación; paquetes; una evaluación vigente por producto; arrays y vacíos acordados; Python/SQL sin bibliotecas; resultados null por error con continuidad; tres salidas y reintentos fijados. Demo local con UI, biblioteca compartida, notebook y tests sintéticos. UI termina en publicación; operación productiva externa. Ver [decisiones actuales](cierre-de-diseno.md).
