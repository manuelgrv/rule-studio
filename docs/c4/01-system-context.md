> HISTÓRICO — boceto sustituido; no usar para implementación. Ver [modelo LikeC4 vigente](architecture.c4) y [guía de vistas](README.md). Incluye decisiones antiguas deliberadamente conservadas como historial.

# C4 level 1 — system context

```mermaid
flowchart LR
  analyst["Persona: Risk Specialist"]
  steward["Persona: Risk Policy — configuración de datos"]
  reviewer["Person: Publication approver / operator"]
  auditor["Person: Auditor — proposed role"]
  manager["System: In-house Rule Manager\nDataset, transformation, rule, and product criteria management"]
  lakehouse["External system: Bank Databricks platform\nSource data, governance, and compute"]
  analyst -->|Authors and experiments| manager
  steward -->|Declares data and variables| manager
  reviewer -->|Reviews and operates releases| manager
  auditor -->|Inspects authorized evidence| manager
  manager -->|Reads data; publishes DSL; executes criteria| lakehouse
```

Databricks is an external platform dependency of the logical Rule Manager system even though it hosts the App and execution runtime. El alcance termina en la tabla de resultados; no incluye sistemas consumidores externos.
