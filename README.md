# Rule Studio

**Demo online:** [Abrir Rule Studio](https://inhouse-rule-manager-demo.manuelrodval.chatgpt.site/)

El sitio es público: cualquier persona con el enlace puede acceder. Para utilizar un espacio de trabajo y guardar ediciones, la aplicación solicita iniciar sesión con ChatGPT.

Rule Studio es un entorno para definir datos de entrada, construir variables reutilizables y crear reglas de evaluación mediante herramientas visuales, Python y SQL. La lógica se expresa en DSL JSON tipadas que pueden validarse, versionarse e interpretarse fuera de la interfaz.

El repositorio incluye una aplicación web, una biblioteca Python y notebooks con datos sintéticos. La demo funciona en un único OpenAI Sites: ejecuta los motores en el navegador y conserva las ediciones en almacenamiento del sitio, sin un servicio FastAPI externo.

[Especificación DSL](docs/dsl/v0.1.md) · [Arquitectura de la demo](docs/demo-sites.md)

> Estado: MVP funcional para diseño y experimentación. Los perfiles de la demo son simulados; la integración con infraestructura productiva es una etapa posterior.

## Funcionalidades

| Módulo | Funcionalidad |
| --- | --- |
| Selección de inputs | Catálogo de fuentes y campos, selección de secciones del consolidado, esquema tipado y configuración JSON de relaciones encadenadas 1:1 y 1:N. |
| Variables virtuales | Expresiones aritméticas, agregaciones sobre arrays, dependencias entre variables, inferencia de tipos y catálogo de cálculos reutilizables. |
| Estudio de reglas | Autoría visual, Python y SQL restringidos; reglas booleanas y composición de productos con operadores lógicos. |
| Aprobaciones | Borradores, propuestas, rechazo con motivo, publicación automática tras aprobación e historial de versiones. |
| Laboratorio | Consolidación y evaluación de datos sintéticos en DuckDB-WASM, resultados por cliente/producto y trazas de variables y reglas. |

La interfaz utiliza React, TypeScript y componentes shadcn, con textos en español. El selector de perfiles permite recorrer los permisos de creación de inputs, variables, reglas y aprobación dentro del espacio de cada visitante.

## Arquitectura actual

~~~mermaid
flowchart LR
    subgraph Browser["Navegador"]
        UI["Rule Studio · React / shadcn"]
        PY["Pyodide · biblioteca rule_manager"]
        DB["DuckDB-WASM · datos y resultados"]
        UI -->|Compilar e interpretar DSL| PY
        UI -->|Materializar y consultar| DB
    end
    subgraph Sites["OpenAI Sites"]
        API["API · Cloudflare Workers"]
        D1["D1 · borradores, versiones y auditoría"]
        API --> D1
    end
    UI -->|Guardar, proponer y aprobar| API
~~~

- **Biblioteca compartida:** Pyodide carga el código Python existente para compilar e interpretar las DSL. El editor visual produce expresiones para esa misma biblioteca.
- **Procesamiento en el navegador:** DuckDB-WASM consolida las fuentes sintéticas. Los resultados de los experimentos son temporales y pueden exportarse como JSON.
- **Persistencia del sitio:** D1 guarda el espacio de cada identidad ChatGPT, con control de revisiones para evitar sobrescrituras concurrentes.
- **Ejecución local alternativa:** la biblioteca también funciona con Python y DuckDB nativos desde scripts y notebooks, sin requerir Sites.

Los diseños de integración con Databricks Apps, Lakehouse, Lakebase y Artifactory se conservan en [docs/](docs/README.md). Describen el destino previsto; la demo no requiere esos servicios.

## Inicio rápido: biblioteca y notebooks

Requisitos: Python **3.11 o superior** y **uv**. Ejecuta desde la raíz del repositorio:

~~~sh
uv sync --extra dev
uv run rule-manager-demo
~~~

La demo genera 30.000 clientes sintéticos con Faker, consolida sus inputs y evalúa tres productos. Crea `data/banking.duckdb` y exporta las DSL, el plan SQL y el consolidado Parquet a `artifacts/demo/`.

Repetir la misma ejecución reutiliza los resultados. Para cambiar el tamaño o la semilla, utiliza otra base:

~~~sh
uv run rule-manager-demo --database data/small.duckdb --clients 100
~~~

Para generar únicamente las tablas fuente en una base nueva:

~~~sh
uv run python scripts/generate_data.py --database data/sources.duckdb --clients 30000
~~~

El generador de fuentes no reemplaza tablas existentes. Las bases locales y los artefactos de ejecución están excluidos de Git; los recursos sintéticos que necesita la web se distribuyen en `web/public/demo/`.

Los notebooks documentan el flujo completo:

1. [Datos y consolidado](notebooks/01_datos_y_consolidado.ipynb): generación sintética, relaciones y estructuras anidadas.
2. [Compilación de DSL](notebooks/02_compilacion_dsl.ipynb): equivalencia visual/Python/SQL y diagnósticos.
3. [Evaluación y trazabilidad](notebooks/03_evaluacion_y_trazabilidad.ipynb): resultados, errores parciales e idempotencia.

Para ejecutarlos y actualizar sus salidas:

~~~sh
uv run python scripts/run_notebooks.py
~~~

El ejecutor usa el Python del proyecto sin instalar un kernel global. También puedes abrir los notebooks con el intérprete de `.venv`.

## Inicio rápido: aplicación web

Requisitos adicionales: Node.js **22.13 o superior**, npm y conexión a internet para descargar dependencias y los runtimes WebAssembly.

Desde la raíz, prepara los recursos de la demo:

~~~sh
uv sync --extra dev
uv run python scripts/prepare_web_demo.py
~~~

Este script genera un conjunto sintético independiente de 30.000 clientes, exporta las fuentes a Parquet y empaqueta la biblioteca Python. Actualiza los recursos generados de `web/public/demo/`; vuelve a ejecutarlo cuando cambie la biblioteca.

Después inicia la web:

~~~sh
cd web
npm ci
npx wrangler d1 migrations apply DB --local --config wrangler.local.json
npm run dev
~~~

Abre la URL que indique el servidor y utiliza el enlace de inicio de sesión local. El plugin de Sites proporciona una identidad de prueba para desarrollo; el sitio alojado utiliza la identidad de ChatGPT.

### Recorrido sugerido

1. Selecciona el perfil de **Inputs**, revisa el consolidado, valida y propone su publicación.
2. Cambia al perfil de **Aprobación** y aprueba los inputs.
3. Utiliza **Variables** para editar cálculos y guardarlos; utiliza **Reglas** para construir reglas y productos.
4. Ejecuta un experimento en el **Laboratorio** y consulta resultados y trazas.
5. Propón el paquete de evaluación y apruébalo con el perfil de **Aprobación**.

La publicación guarda la DSL aprobada. Las ejecuciones productivas se controlan externamente; el laboratorio solo ejecuta experimentos.

### Compilación y alojamiento

Desde `web/`:

~~~sh
npm run build
~~~

El proyecto genera una aplicación compatible con Cloudflare Workers. El despliegue en Sites usa `.openai/hosting.json`, la vinculación D1 y las migraciones de `web/drizzle/`. La configuración incluida identifica la instancia de esta demo; un despliegue propio necesita su propia configuración de Sites. Las credenciales de publicación no forman parte del repositorio.

## Contratos DSL

Hay dos documentos JSON independientes:

| Documento | Contenido |
| --- | --- |
| [Inputs consolidados](examples/inputs.json) | Fuentes, campos, tipos, joins, mappings y esquema de salida, incluidos objetos y arrays de objetos. |
| [Variables y evaluaciones](examples/evaluations.json) | Contrato de inputs, constantes, variables, reglas y composición de productos. |

El paquete de evaluación referencia la definición de inputs por identificador, versión y hash del esquema. La compilación detecta referencias inválidas, incompatibilidades de tipos, ciclos y construcciones fuera del lenguaje admitido.

Las funciones de autoría deben retornar un booleano. Un error durante la evaluación genera un resultado `null` y un diagnóstico para la regla o producto afectado; los demás productos continúan. Ese `null` indica un error de ejecución, no un retorno permitido en la función fuente.

Consulta la [especificación implementada v0.1](docs/dsl/v0.1.md) para operadores, tipos, nulos y restricciones.

### Uso de la biblioteca

~~~python
from rule_manager.api import compile_rule
from rule_manager.examples import input_definition, evaluation_definition
from rule_manager.validation import validate_evaluations

inputs = input_definition()
package = evaluation_definition(inputs)
_, environment = validate_evaluations(package, inputs)

source = '''def regla(inputs) -> bool:
    return inputs["age"] >= 18
'''

artifact = compile_rule(source, "python", environment)
print(artifact.to_dict())
~~~

`compile_rule` también acepta `sql` y `visual`. Devuelve la expresión DSL, el código fuente, su hash y la versión del compilador. El nombre de distribución Python sigue siendo `inhouse-rule-manager` y el módulo importable es `rule_manager`.

Para generar el paquete distribuible, incluidos sus esquemas JSON:

~~~sh
uv build
~~~

## Datos y trazabilidad

Las fuentes de ejemplo son `clients`, `finances`, `accounts`, `movements` y `loans`. Todos sus registros son sintéticos.

| Salida | Python / DuckDB local | Demo web / DuckDB-WASM |
| --- | --- | --- |
| Input consolidado por cliente | `consolidated_inputs` | `consolidated_input` |
| Resultado por cliente, producto y ejecución | `evaluations` | `product_evaluations` |
| Variables materializadas por cliente y ejecución | `virtual_variables` | `virtual_variables` |
| Reglas evaluadas y sus resultados | `rule_results` | `rule_results` |

El adaptador local también registra ejecuciones en `rm_runs` y la semilla/tamaño de los datos en `synthetic_manifest`. El consolidado contiene estructuras tipadas y listas anidadas. La exportación local a Parquet particiona por `execution_id`; las tablas internas de DuckDB no se particionan físicamente por esa columna.

## Verificación

Desde la raíz:

~~~sh
uv run pytest -q
~~~

Desde `web/`:

~~~sh
npx tsc --noEmit
node --experimental-strip-types tests/workflow.mts
node tests/wasm.mjs
~~~

Con el servidor de desarrollo activo en `http://localhost:3000`, ejecuta en otra terminal desde `web/`:

~~~sh
node tests/api.mjs
~~~

Las pruebas cubren el lenguaje y el adaptador local, permisos de demostración, versiones publicadas inmutables, persistencia y conflictos de revisión. La prueba WASM ejecuta los motores reales y comprueba que 90.000 decisiones sobre 30.000 clientes coincidan con los resultados esperados de la implementación nativa, incluidos los errores parciales.

## Estructura del proyecto

Todo el código se mantiene en un único repositorio Git desde la raíz. La carpeta `web/` es parte del proyecto, no un submódulo ni un repositorio independiente; sus dependencias y artefactos locales se excluyen mediante su `.gitignore`.

~~~text
src/rule_manager/    Biblioteca Python, compiladores, intérprete y esquemas JSON
examples/           Ejemplos de las dos DSL
scripts/            Generación sintética, recursos web y ejecución de notebooks
notebooks/          Demos reproducibles del lenguaje y la evaluación
tests/              Pruebas Python
web/                Rule Studio, API de persistencia y pruebas WebAssembly
docs/               Especificaciones, acuerdos y arquitectura
docs/c4/            Vistas de arquitectura LikeC4
~~~

## Límites del MVP

- Los perfiles son simulados dentro del espacio privado de cada visitante. No implementan separación real de funciones entre personas.
- La validación semántica ocurre en el navegador. Una publicación productiva necesita validación independiente en un entorno confiable y permisos asociados a identidades reales.
- Los borradores e historial se conservan en D1; las tablas y los resultados del laboratorio se regeneran al recargar el navegador.
- Python y SQL son subconjuntos restringidos. No se admiten imports, librerías de usuario ni ejecución arbitraria de código fuente. PySpark y pandas no forman parte del lenguaje de autoría del MVP.
- El selector visual de inputs trabaja con secciones del ejemplo; la configuración detallada de nodos y joins se realiza mediante el editor JSON.
- Los cambios incompatibles de inputs con productos vigentes requieren una migración coordinada, todavía pendiente.
- La demo no es un motor distribuido ni una validación de capacidad para 30 millones de clientes. Las integraciones productivas previstas no están implementadas.

## Documentación

- [Demo actual en Sites](docs/demo-sites.md)
- [Especificación del lenguaje implementado](docs/dsl/v0.1.md)
- [Módulos y contratos funcionales](docs/modulos-vigentes.md)
- [Diagramas LikeC4](docs/c4/README.md)
- [Índice de diseño y decisiones](docs/README.md)

Este README y la documentación de la demo describen la implementación actual. Los documentos de planificación también contienen propuestas e historial; no deben interpretarse como una lista de integraciones ya disponibles.
