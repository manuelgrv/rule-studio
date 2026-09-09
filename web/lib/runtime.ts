import type { AsyncDuckDB, AsyncDuckDBConnection } from '@duckdb/duckdb-wasm';
export type Doc = Record<string, any>;
let compiler: Worker | undefined;
let serial = 0;
const requests = new Map<
  number,
  {
    resolve: (x: any) => void;
    reject: (e: Error) => void;
    timer: ReturnType<typeof setTimeout>;
  }
>();
export function compile(payload: Doc): Promise<any> {
  if (!compiler) {
    compiler = new Worker('/compiler.worker.js');
    compiler.onmessage = ({ data }) => {
      const r = requests.get(data.id);
      if (!r) return;
      clearTimeout(r.timer);
      requests.delete(data.id);
      data.ok
        ? r.resolve(data.result)
        : r.reject(new Error(`${data.error.code}: ${data.error.message}`));
    };
    compiler.onerror = () => {
      for (const r of requests.values()) {
        clearTimeout(r.timer);
        r.reject(
          new Error(
            'No se pudo iniciar el compilador. Comprueba la conexión y reintenta.',
          ),
        );
      }
      requests.clear();
      compiler?.terminate();
      compiler = undefined;
    };
  }
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      requests.delete(id);
      reject(
        new Error(
          'El compilador excedió el tiempo disponible. Recarga para reintentar.',
        ),
      );
    }, 180000);
    requests.set(id, { resolve, reject, timer });
    compiler!.postMessage({ id, payload });
  });
}
let database:
  | Promise<{ db: AsyncDuckDB; con: AsyncDuckDBConnection }>
  | undefined;
export const tables = ['clients', 'finances', 'accounts', 'movements', 'loans'];
export async function getDatabase() {
  return (database ||= (async () => {
    const duckdb = await import('@duckdb/duckdb-wasm');
    const bundle = await duckdb.selectBundle(duckdb.getJsDelivrBundles());
    const url = URL.createObjectURL(
      new Blob([`importScripts(${JSON.stringify(bundle.mainWorker)});`], {
        type: 'text/javascript',
      }),
    );
    const worker = new Worker(url);
    const db = new duckdb.AsyncDuckDB(new duckdb.VoidLogger(), worker);
    try {
      await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    } finally {
      URL.revokeObjectURL(url);
    }
    const con = await db.connect();
    for (const table of tables) {
      const r = await fetch(`/demo/${table}.parquet`);
      if (!r.ok) throw new Error(`No se pudo cargar ${table}`);
      await db.registerFileBuffer(
        `${table}.parquet`,
        new Uint8Array(await r.arrayBuffer()),
      );
      await con.query(
        `CREATE TABLE ${table} AS SELECT * FROM '${table}.parquet'`,
      );
    }
    return { db, con };
  })().catch((e) => {
    database = undefined;
    throw e;
  }));
}
export async function previewTable(table: string) {
  if (!tables.includes(table)) throw new Error('Tabla no disponible');
  const { con } = await getDatabase();
  const result = await con.query(
    `SELECT CAST(to_json(t) AS VARCHAR) AS row FROM (SELECT * FROM ${table} LIMIT 8) t`,
  );
  return result.toArray().map((r) => JSON.parse(r.row));
}
export async function experiment(
  inputs: Doc,
  evaluations: Doc,
  catalog: Doc[],
  limit: number,
) {
  if (![100, 1000, 30000].includes(limit)) throw new Error('Muestra no válida');
  const { sql } = await compile({
    action: 'validate',
    inputs,
    evaluations,
    catalog,
  });
  const { db, con } = await getDatabase();
  const id = crypto.randomUUID();
  await con.query(
    `CREATE OR REPLACE TABLE consolidated_input AS SELECT '${id}' execution_id, CURRENT_DATE processing_date, ${Number(inputs.definition_version)} version, '${String(inputs.created_by).replaceAll("'", "''")}' created_by, * FROM (${sql})`,
  );
  // Keep decimals in JSON text until Python parses them exactly.
  const selected = await con.query(
    `SELECT CAST(to_json(t) AS VARCHAR) AS row FROM (SELECT client,fields FROM consolidated_input ORDER BY client LIMIT ${limit}) t`,
  );
  const rows = selected.toArray().map((r) => r.row);
  const traces: any[] = [];
  for (let i = 0; i < rows.length; i += 500) {
    traces.push(
      ...(await compile({
        action: 'evaluate',
        inputs,
        evaluations,
        catalog,
        rows: `[${rows.slice(i, i + 500).join(',')}]`,
      })),
    );
  }
  const products = traces.flatMap((t) =>
    t.products.map((p: any) => ({
      execution_id: id,
      client: t.client,
      product: p.id,
      version: p.version,
      accepted: p.value,
      details: JSON.stringify({ rules: p.rules, error: p.error }),
    })),
  );
  const vars = traces.map((t) => ({
    execution_id: id,
    client: t.client,
    details: JSON.stringify(t.variables),
  }));
  const rules = traces.map((t) => ({
    execution_id: id,
    client: t.client,
    details: JSON.stringify(t.rules),
  }));
  for (const [name, data] of [
    ['product_evaluations', products],
    ['virtual_variables', vars],
    ['rule_results', rules],
  ] as const) {
    await db.registerFileText(`${name}.json`, JSON.stringify(data));
    await con.query(
      `CREATE OR REPLACE TABLE ${name} AS SELECT * FROM read_json_auto('${name}.json')`,
    );
  }
  return {
    id,
    clients: traces.length,
    products,
    variables: vars,
    rules,
    summary: evaluations.products.map((p: Doc) => ({
      product: p.id,
      accepted: products.filter(
        (v) => v.product === p.id && v.accepted === true,
      ).length,
      denied: products.filter((v) => v.product === p.id && v.accepted === false)
        .length,
      errors: products.filter((v) => v.product === p.id && v.accepted === null)
        .length,
    })),
  };
}
