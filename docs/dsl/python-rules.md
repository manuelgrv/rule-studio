# Autoría de reglas mediante funciones Python

Referencia implementada: [DSL v0.1](v0.1.md), esquemas y ejemplos ejecutados. Las propuestas/fragmentos anteriores que siguen se conservan como contexto de diseño; v0.1 define la sintaxis efectiva.
## Confirmado y propuesto

Python/SQL a DSL ya estaba considerado. Se confirma ahora que la autoría Python declara una función cuyo único tipo de resultado es booleano. La firma y el subconjunto siguientes son propuestas iniciales.

```python
def regla(inputs, variables, constants) -> bool:
    return inputs["age"] >= constants["minimum_age"]
```

Ejemplo sintético con campos enteros no nulos. Los parámetros representan espacios de nombres tipados del cliente; no acceso libre a tablas ni al entorno del proceso.

La anotación -> bool no garantiza el retorno. El compilador verifica todos los caminos y rechaza números, cadenas, None, caminos sin retorno y expresiones nullable sin tratamiento explícito. No convierte Series o Columns a booleano implícitamente.

## Subconjunto recomendado

Primera iteración: una función de nivel superior, referencias mediante claves literales, literales tipados, comparaciones, and/or/not y asignaciones locales simples. Añadir if/else acotado cuando ambos caminos puedan traducirse y tengan retorno definido. Las variables reutilizables y trazables pertenecen al módulo 2; una variable local no se cataloga automáticamente.

Rechazar bucles, recursión, clases, decoradores, generadores, código dinámico, globals externos, acceso a archivos/red y llamadas no catalogadas. Analizar la fuente sin ejecutarla.

Confirmado para MVP: Python y SQL sin bibliotecas de usuario; no se admiten imports. Sustituye la whitelist anterior de PySpark/pandas. El backend interno puede usar PySpark y otras dependencias. Las operaciones permitidas de la DSL no habilitan llamadas arbitrarias.

## Compilación

1. Parsear AST y comprobar firma/sintaxis sin ejecutar código.
2. Resolver referencias al input fijado, variables y constantes.
3. Inferir tipos y verificar todos los retornos.
4. Traducir a expresiones de la DSL canónica.
5. Conservar fuente, hash, ubicación de errores y versión de compilador.
6. Ejecutar DSL con semántica compartida con low-code/SQL.

Propuesta: generar operaciones distribuidas de Spark, evitando invocar una función Python por cada fila de los 30 millones de clientes. La función describe la lógica de un cliente; no impone ejecución fila por fila.

## Complejidad

Moderada para un subconjunto cerrado de expresiones booleanas; alta para Python/pandas/PySpark general. El trabajo principal está en tipos, control de flujo, nulos, diagnósticos y equivalencia entre motores. No basta una anotación o probar la función con algunos ejemplos.

Pruebas a implementar: equivalencia con low-code, retorno numérico/nulo, camino sin retorno, referencia inexistente, imports no permitidos, llamadas con efectos externos, comparaciones nullable y ramas.

Pendientes de implementación: catálogo y sintaxis exacta de llamadas propias de la DSL, control de flujo acotado, precisión y elementos null dentro de arrays. No queda pendiente habilitar imports en este MVP.

La función válida retorna booleano. Si la ejecución falla, el motor registra resultado null con diagnóstico para la regla y producto afectados, continuando otros productos. Esto no permite return None en la fuente.
