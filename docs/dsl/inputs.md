# DSL de inputs consolidados

Referencia implementada: [DSL v0.1](v0.1.md), esquemas y ejemplos ejecutados. Las propuestas/fragmentos anteriores que siguen se conservan como contexto de diseño; v0.1 define la sintaxis efectiva.
## Contrato confirmado

El módulo 1 selecciona campos existentes del catálogo lakehouse y configura la información semiestructurada por cliente. Genera DSL descargable y versionado por usuario, aprobado antes de sustituir la única definición productiva vigente. La biblioteca de Artifactory lo procesa en el lakehouse.

Se mantiene la clave lógica (execution_id, date, client, version), partición execution_id, fecha de procesamiento, versión de definición y metadatos de procedencia. El input es compartido entre productos.

## Secciones propuestas

| Sección | Contenido |
| --- | --- |
| Cabecera común | Identidad y versiones |
| catalog_snapshot | Referencia y hash del catálogo/esquema validado |
| sources | Fuentes autorizadas, alias, campos y clave de cliente raíz |
| joins | Claves, dirección, cardinalidades y recorridos |
| output_schema | Esquema tipado del campo semiestructurado |
| mappings | Correspondencia entre fuentes y rutas de salida |

Las uniones encadenadas permiten cliente → cónyuge → ingresos. Una relación 1:1 genera valor o struct; 1:N genera lista de structs. Consolidar cada relación múltiple antes de combinarla con otras para evitar multiplicar filas del cliente.

La aritmética reutilizable pertenece al módulo 2.

## Fragmento ilustrativo

```json
{
  "kind": "consolidated_inputs",
  "dsl_version": "0.1",
  "definition_id": "client_inputs",
  "definition_version": 1,
  "sources": [
    {"id": "clients", "table_ref": "synthetic_clients", "client_key": "client_id", "fields": ["client_id", "age"]}
  ],
  "joins": [],
  "output_schema": {
    "type": "struct",
    "fields": {"age": {"type": "integer", "nullable": false}}
  },
  "mappings": [{"target": "age", "source": "clients.age"}]
}
```

Omite procedencia y snapshot. table_ref se resuelve contra fuentes autorizadas.

## Validaciones y pendientes

Rechazar campos desconocidos, rutas duplicadas, tipos incompatibles y uniones lógicamente inconsistentes. La unicidad declarada requiere control en ejecución: no seleccionar arbitrariamente una coincidencia si una unión 1:1 encuentra varias.

Confirmado: 1:1 sin coincidencia produce null solo si el contrato lo permite; varias coincidencias causan error. Pendientes: orden y tamaño de listas, filtros temporales y duplicados de fuente.

## Arrays de objetos — confirmado

El esquema declara el tipo de cada nodo, incluidos objetos anidados, arrays y sus elementos. Los arrays pueden contener objetos con campos escalares, otros objetos u otros arrays. Declarar por separado la nulabilidad del array, de sus elementos y de cada campo del objeto.

Cada array derivado de una relación 1:N se vincula a la relación de origen declarada en joins y mappings. Si no hay registros relacionados, se materializa `[]`: no `null`, ni un objeto con todos sus campos nulos, ni `[null]`. Esta regla no convierte fallos de lectura o de ejecución en colecciones vacías.

La consolidación conserva una fila por cliente dentro de la ejecución/fecha/versión. Varias relaciones 1:N no deben producir un producto cartesiano ni duplicar sus elementos al combinarse.

Fragmento propuesto de output_schema para cuentas de un cliente:

```json
{
  "type": "struct",
  "nullable": false,
  "fields": {
    "cuentas": {
      "type": "array",
      "nullable": false,
      "items": {
        "type": "struct",
        "nullable": false,
        "fields": {
          "id_cuenta": {"type": "string", "nullable": false},
          "saldo": {"type": "decimal", "precision": 18, "scale": 2, "nullable": true}
        }
      }
    }
  }
}
```

Casos de conformidad pendientes de implementar: cero coincidencias produce []; una o varias coincidencias conservan sus objetos; dos relaciones independientes de tamaños 2 y 3 producen arrays de tamaños 2 y 3 en una sola fila; estructuras anidadas respetan tipos y nulabilidad. Confirmado: suma/conteo sobre [] es 0; min/max/promedio es null; existe es false y todos es true.
