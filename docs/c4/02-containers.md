> HISTÓRICO — boceto sustituido; no usar para implementación. Ver [modelo LikeC4 vigente](architecture.c4) y [guía de vistas](README.md). Incluye decisiones antiguas deliberadamente conservadas como historial.

# C4 level 2 — containers

```mermaid
flowchart TB
  user["Person: Authorized bank user"]
  sources[("External data: Existing lakehouse sources")]
  subgraph system["In-house Rule Manager — hosted on bank Databricks platform"]
    app["Container: Databricks App\nFour modules; frontend stack TBD"]
    workflow[("Data store: Authoring and workflow\nPhysical technology TBD")]
    registry[("Data store: Published DSL registry\nLakehouse tables")]
    compiler["Container: Compiler worker — proposed\nSource-to-DSL and DSL-to-execution compilation"]
    artifacts[("Data store: Compiled artifacts — proposed\nStorage TBD")]
    runtime["Container: Execution workers — proposed\nPython processing: consolidation, transformations, rule engines, interpreter"]
    datasets[("Data store: Consolidated input\nSingle lakehouse table: execution/date/client/version; partitioned by execution ID")]
    results[("Data store: Product evaluation results\nSingle lakehouse table")]
  end
  user -->|HTTPS| app
  app -->|Read/write drafts and reviews| workflow
  app -->|Automatically publish approved release| registry
  app -->|Request compilation| compiler
  compiler -->|Read published release| registry
  app -->|Pass validated experiment or dataset definition| compiler
  compiler -->|Write generated plan| artifacts
  app -->|Request run and inspect status| runtime
  runtime -->|Read pinned plan| artifacts
  runtime -->|Read authorized inputs| sources
  runtime -->|Materialize and read| datasets
  runtime -->|Write results and provenance| results
  app -->|Read permitted experiment results| results
```

Experiment snapshots may be passed directly to the compiler; only production releases must be published in the DSL registry. Registry reads by the compiler refer to published releases. Arrows describe responsibilities, not final transport protocols. Production runs are scheduled batches; experiments run on demand. Identity integration remains to be designed.
