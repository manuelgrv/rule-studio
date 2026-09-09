# Especificaciones DSL

Referencia implementada: [DSL v0.1](v0.1.md), esquemas y ejemplos ejecutados. Las propuestas/fragmentos anteriores que siguen se conservan como contexto de diseño; v0.1 define la sintaxis efectiva.
Estado: dos contratos y semánticas principales acordados en [cierre de diseño](../cierre-de-diseno.md); sintaxis formal v0.1 y compiladores pendientes de implementación.

1. [Inputs consolidados](inputs.md): selección, uniones, estructura y materialización por cliente.
2. [Variables y evaluaciones](evaluations.md): variables, constantes, reglas y composición de productos en un documento autocontenido.

Ambas usan JSON y el [contrato común](common.md). El [contrato Python](python-rules.md) describe la autoría de funciones booleanas.

Esta organización sustituye las propuestas anteriores de tres archivos JSON o cuatro DSL independientes. Las entidades conservan IDs y versiones propias dentro de cada documento.

Siguiente etapa: resolver semánticas pendientes, publicar JSON Schema y crear pruebas de conformidad. Los ejemplos son fragmentos ilustrativos, no fixtures completos ni un lenguaje ya ejecutable.
