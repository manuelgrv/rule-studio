# Rule Studio: documentación y diseño

Estado: biblioteca Python, notebooks y demo web implementados. La demo utiliza DuckDB-WASM, Pyodide y persistencia D1 en Sites, e incluye un flujo de aprobación con perfiles simulados. Consulta el [README del proyecto](../README.md) y la [arquitectura de la demo](demo-sites.md) para el alcance actual.

This directory is the source of truth for project planning. Los acuerdos actuales están en cierre-de-diseno.md; las propuestas de implementación siguen identificadas como tales.

| File | Purpose |
| --- | --- |
| [Cierre de diseño](cierre-de-diseno.md) | Auditoría de coherencia y decisiones pendientes antes de construir |
| [Módulos vigentes](modulos-vigentes.md) | Tres módulos, descargas JSON y tres tablas de salida |
| [Specification](specification.md) | Scope, modules, workflows, and proposed acceptance criteria |
| [Especificaciones DSL](dsl/README.md) | Dos contratos JSON y autoría Python booleana |
| [Domain and DSL](domain-and-dsl.md) | Versioned entities, language boundaries, and evaluation semantics |
| [Language scope](language-scope.md) | Low-code complexity and Python/SQL-to-DSL compilation |
| [Data contracts](data-contracts.md) | Consolidated input table, chained joins, transformations, and result table |
| [Entornos y operación](entornos-y-operacion.md) | Decisiones vigentes: prod/edv, Lakebase, JSON, roles, trazabilidad y recomendación de stack |
| [Synthetic MVP](synthetic-mvp.md) | Fictional data, demonstration scenarios, and DSL specification checklist |
| [Architecture](architecture.md) | Databricks integration, compiler, execution, and governance |
| [Decisions and questions](decisions-and-questions.md) | Confirmed decisions, proposals, and discovery backlog |
| [C4 architecture](c4/README.md) | Context, container, and component diagrams |

Estos documentos conservan los acuerdos y sus consecuencias arquitectónicas, incluidas propuestas e historial. La demo ya tiene implementación y despliegue; las integraciones productivas descritas en el diseño siguen siendo una etapa posterior.

Precedencia: cierre-de-diseno.md registra los acuerdos más recientes, propagados a modulos-vigentes.md y dsl/. cierre-de-diseno.md centraliza pendientes actuales; no los convierte en requisitos aprobados. Los Mermaid antiguos son históricos; LikeC4 es el modelo visual vigente.

Implementación actual del lenguaje: [DSL v0.1](dsl/v0.1.md). La biblioteca y notebooks ya existen; el aviso histórico sobre planificación no impide esta etapa de construcción autorizada.
