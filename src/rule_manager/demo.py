import argparse
import json
from pathlib import Path
import duckdb
from .synthetic import generate_banking_data,ALLOWED_TABLES
from .examples import input_definition,evaluation_definition
from .duckdb_backend import DuckDBBackend,json_text

def run_demo(database,clients=30000,seed=20260909,artifacts=None):
    database=Path(database)
    database.parent.mkdir(parents=True,exist_ok=True)
    with duckdb.connect(str(database)) as con:
        present=con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='synthetic_manifest'").fetchone()[0]
        if present:
            previous=con.execute("SELECT seed,clients FROM synthetic_manifest").fetchone()
            if previous!=(seed,clients): raise ValueError("Existing fixture has another seed/size; use a different database")
        else: generate_banking_data(con,clients,seed)
        backend=DuckDBBackend(con,ALLOWED_TABLES)
        inputs=input_definition();evaluation=evaluation_definition(inputs)
        materialized=backend.materialize(inputs,"input-demo-001","2026-09-09")
        evaluated=backend.evaluate(evaluation,"input-demo-001","evaluation-demo-001")
        summary=con.execute("""SELECT product, count(*) clients, count(*) FILTER (WHERE result) accepted,
          count(*) FILTER (WHERE result=false) denied, count(*) FILTER (WHERE result IS NULL) errors
          FROM evaluations GROUP BY product ORDER BY product""").fetchall()
        if artifacts:
            directory=Path(artifacts);directory.mkdir(parents=True,exist_ok=True)
            (directory/"inputs.json").write_text(json_text(inputs)+"\n")
            (directory/"evaluations.json").write_text(json_text(evaluation)+"\n")
            (directory/"consolidation.sql").write_text(con.execute("SELECT json_extract_string(details,'$.sql') FROM rm_runs WHERE kind='input'").fetchone()[0]+"\n")
            backend.export_inputs("input-demo-001",directory/"consolidated")
        return {"database":str(database.resolve()),"input":materialized,"evaluation":evaluated,"products":summary}

def main():
    parser=argparse.ArgumentParser(description="Local banking DSL demonstration")
    parser.add_argument("--database",default="data/banking.duckdb")
    parser.add_argument("--clients",type=int,default=30000)
    parser.add_argument("--seed",type=int,default=20260909)
    parser.add_argument("--artifacts",default="artifacts/demo")
    args=parser.parse_args()
    print(json.dumps(run_demo(args.database,args.clients,args.seed,args.artifacts),indent=2,ensure_ascii=False))

if __name__ == "__main__":
    main()
