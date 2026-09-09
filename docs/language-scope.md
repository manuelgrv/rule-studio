# Alcance de autoría y paridad

## Confirmado para MVP

Low-code, Python restringido y SQL producen la misma DSL canónica. Sin bibliotecas/imports en código de usuario. La restricción anterior «solo PySpark/pandas» queda sustituida; las dependencias internas de la aplicación y motores sí están permitidas.

Python declara función con retorno booleano, AST y validación estática de todos los caminos sin ejecutar fuente. SQL admite un subconjunto de expresiones traducibles y tipadas sobre el input declarado, sin lecturas arbitrarias ni DDL/DML. La gramática exacta y catálogo de llamadas permitidas se fijan al implementar.

## Operaciones

Referencias tipadas, constantes, comparaciones, AND/OR/NOT, manejo explícito de null y aritmética. Variables encadenadas sin ciclos. Arrays del mismo cliente: suma, conteo, mínimo, máximo, promedio y predicados existe/todos. Estadísticas complejas y agregación entre clientes fuera del MVP.

Las funciones propias del lenguaje DSL no se consideran bibliotecas importadas. Sintaxis Python/SQL para operadores sobre arrays se definirá como parte de la especificación formal, sin admitir llamadas arbitrarias.

## Vacíos y errores

1:N ausente → []; 1:1 ausente → null solo si el contrato lo permite; múltiples coincidencias 1:1 → error. Arrays vacíos: suma/conteo=0; min/max/promedio=null; existe=false; todos=true.

La función de regla válida retorna true/false, no None. Error al ejecutar → resultado persistido null con estado/diagnóstico. El producto afectado queda null aunque otra rama lógica pudiera decidirlo; los demás productos continúan. Todos los resultados de reglas seleccionadas se registran.

## Implementación pendiente

Sintaxis de if/else acotado, resolución de nombres, precisión y casts, elementos null en arrays no vacíos, orden/limites y diagnósticos con ubicación. No ejecutar una fuente no traducible como fallback. Tests deben demostrar paridad entre formas de autoría y ejecución con la misma biblioteca.

Ver [Python](dsl/python-rules.md), [evaluaciones](dsl/evaluations.md) y [contrato común](dsl/common.md).
