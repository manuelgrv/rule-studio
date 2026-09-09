# Demo en un único Sites

La demo web usa React, TypeScript, Vite/Vinext y componentes shadcn. Sites aloja la UI y una API de persistencia en Workers. D1 guarda un espacio independiente por identidad ChatGPT: borradores, propuestas, versiones publicadas y auditoría. DuckDB-WASM materializa datos sintéticos en el navegador. Pyodide carga la misma biblioteca `rule_manager` para compilar Python, SQL y expresiones visuales, y para interpretar evaluaciones.

## Alcance implementado

- Selección de secciones del input, catálogo de tablas/campos, muestra de fuentes y editor JSON para configurar tipos, estructura y joins encadenados 1:1/1:N.
- Variables con expresiones visuales, dependencias, tipos inferidos y compilación.
- Reglas visuales, Python restringido y SQL; productos compuestos con operadores lógicos. Dos DSL separadas: inputs y paquete de variables/evaluaciones, enlazadas por contrato.
- Guardado, propuesta, rechazo y aprobación con publicación automática de snapshots. Permisos diferenciados por perfil sintético; una evaluación vigente por producto.
- Laboratorio explícitamente experimental: consolidado de 30.000 clientes y evaluación de muestras de 100, 1.000 o 30.000; tres tablas de salidas y exportación JSON. Las ejecuciones productivas siguen fuera de la UI.

## Límites deliberados

Los perfiles son personajes intercambiables dentro del espacio del visitante; no representan segregación bancaria real entre personas. La API controla las transiciones según esos perfiles, pero la compilación semántica ocurre en el navegador y no es una certificación confiable para producción. Una implementación bancaria necesitará validación independiente en servidor y permisos ligados a identidades reales.

DuckDB vive en memoria del navegador. Datos y resultados se regeneran al recargar; D1 conserva las ediciones e historial. Los runtimes WASM se descargan de CDN con versiones específicas. No se incluyen PySpark ni pandas. El código de reglas no se ejecuta: se analiza con AST y se convierte a DSL usando la biblioteca existente.

El diseñador sencillo selecciona secciones completas del ejemplo; el JSON permite detalle de nodos y relaciones. Un cambio incompatible en inputs con productos publicados queda bloqueado y requiere definir la migración coordinada en la siguiente etapa. Los errores de reglas/productos se conservan como nulos y los otros productos continúan.

## Desarrollo y verificación

El proyecto mantiene un único repositorio Git en la raíz, incluida la carpeta `web/`. Para futuras publicaciones mediante herramientas de Sites que requieran un repositorio exclusivo de la web, se debe preparar un checkout temporal fuera del proyecto a partir de la versión de `web/` que se vaya a publicar, conservando su `project_id`. No se debe volver a inicializar un repositorio Git dentro de `web/`.

Desde la raíz: `.venv/bin/python scripts/prepare_web_demo.py` genera fuentes sintéticas independientes y empaqueta la biblioteca. Desde `web`: `npm run dev`; `npx wrangler d1 migrations apply DB --local --config wrangler.local.json`; `npm run build`.

Pruebas: `node tests/wasm.mjs` ejecuta DuckDB y Python en WebAssembly, compara las 90.000 decisiones con el motor nativo y valida rechazo de imports/retornos inválidos. `node --experimental-strip-types tests/workflow.mts` valida permisos y publicaciones. `node tests/api.mjs` comprueba API local con la identidad sintética proporcionada por Sites.

WebMCP expone únicamente navegación a los módulos. La validación en un contexto WebMCP real queda pendiente si el entorno no lo proporciona; no afecta al uso manual de la demo.
