> HISTÓRICO — boceto sustituido; no usar para implementación. Ver [modelo LikeC4 vigente](architecture.c4) y [guía de vistas](README.md). Incluye decisiones antiguas deliberadamente conservadas como historial.

# C4 level 3 — Databricks App components

```mermaid
flowchart TB
  user["Person: Authorized bank user"]
  subgraph app["Container: Databricks App"]
    ui["Component: Web UI\nDataset, transformation, rule, product, and review screens"]
    api["Component: Backend request boundary\nAuthentication context and authorization"]
    dataset["Component: Dataset Manager\nSources, chained joins, consolidation DSL"]
    transform["Component: Transformed Field Builder\nArithmetic and aggregations over exposed variables"]
    rule["Component: Rule Manager\nLow-code DSL and Python/SQL-to-DSL compilation"]
    product["Component: Product Evaluation Builder\nComposition and experiments"]
    validation["Component: Shared contract validation\nTypes and dependency compatibility"]
    releases["Component: Version and release workflow\nSingle-person review, automatic publication, activation"]
    execution["Component: Execution adapter\nCompile/run requests and status"]
  end
  store[("Container: Authoring/workflow store")]
  registry[("Container: DSL registry")]
  workers["Containers: Compiler and execution workers"]
  user -->|HTTPS| ui
  ui -->|Authenticated requests| api
  api --> dataset
  api --> transform
  api --> rule
  api --> product
  api --> releases
  dataset --> validation
  transform --> validation
  rule --> validation
  product --> validation
  dataset --> store
  transform --> store
  rule --> store
  product --> store
  releases -->|Validate exact release| validation
  releases --> store
  releases -->|Publish| registry
  releases --> execution
  dataset -->|Materialization request| execution
  product -->|Experiment request| execution
  execution --> workers
```

All components are proposed internal boundaries in one App, not independently deployed services. Backend authorization applies to each operation, including execution requests. Workers enforce their own resource permissions.
