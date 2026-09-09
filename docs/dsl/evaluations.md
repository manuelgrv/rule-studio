# DSL de variables virtuales y evaluaciones

Referencia implementada: [DSL v0.1](v0.1.md), esquemas y ejemplos ejecutados. Las propuestas/fragmentos anteriores que siguen se conservan como contexto de diseño; v0.1 define la sintaxis efectiva.
## Contrato confirmado

Un único JSON descargable contiene variables y evaluaciones con referencia a una versión exacta del input. Incluye las definiciones necesarias para los productos seleccionados, conservando IDs y versiones individuales.

| Sección propuesta | Responsabilidad |
| --- | --- |
| Cabecera común | Identidad y versiones |
| input_contract | ID, versión y hash del esquema de input |
| constants | Valores tipados fijados |
| variables | Expresiones aritméticas por cliente y dependencias |
| rules | Expresiones booleanas no nulas |
| products | Composición exclusivamente lógica de reglas |

Las variables pueden depender de otras sin ciclos. Confirmadas suma, conteo, mínimo, máximo, promedio y condiciones existe/todos sobre arrays del mismo cliente; estadísticas complejas después. Las reglas usan inputs, variables y constantes. Para productos se confirman AND/OR/NOT; no ponderaciones, prioridades ni excepciones individuales.

## Expresiones propuestas

Representar lógica mediante árboles: ref distingue ámbito y campo; literal tiene valor/tipo; op declara operador y argumentos. No almacenar código Python como sustituto de una expresión ejecutable.

Fragmento de regla sintética, con age entero no nulo:

```json
{
  "id": "synthetic_age_check",
  "version": 1,
  "result_type": "boolean",
  "expression": {
    "op": "gte",
    "args": [
      {"ref": {"scope": "input", "path": ["age"]}},
      {"literal": {"type": "integer", "value": 18}}
    ]
  }
}
```

Ejemplo ficticio; no establece criterios bancarios.

## Autoría y ejecución

Low-code y Python/SQL generan el mismo árbol tipado. [Python](python-rules.md) permite declarar una función booleana. Conservar su fuente como procedencia; nunca ejecutar código arbitrario si la traducción falla.

El proceso carga input, calcula variables según dependencias, evalúa reglas y compone productos. Confirmado: evaluar todas las reglas de los productos seleccionados para conservar una traza completa, aunque la composición pudiera cortocircuitarse.

Produce tres salidas correlacionadas por ejecución y versiones:

1. Evaluaciones: una fila por cliente/producto/ejecución.
2. Variables: una fila por cliente/ejecución con colección tipada, versiones y traza.
3. Reglas: una fila por cliente/ejecución con colección de reglas, versiones, resultados y errores.

true = Aceptado; false = Denegado. Error de ejecución = resultado null y diagnóstico técnico en regla/producto afectados. Otros productos continúan. La función de autoría no puede retornar None. No ocultar errores de dependencias mediante cortocircuito de AND/OR. Propuesta: completar una ejecución solo después de verificar sus tres salidas, sin presuponer una transacción entre tablas.
