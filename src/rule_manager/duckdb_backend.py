"""Local adapter. DuckDB executes consolidation SQL; Python interprets evaluation plans."""
import json
from datetime import date
from decimal import Decimal
from . import __version__
from .inputs import CatalogTable, compile_inputs, table_name
from .types import value_as, sql_type
from .validation import canonical_hash
from .engine import EvaluationPlan
from .errors import CompileError, EvaluationError

def from_duck_type(t, is_nullable):
    kind=t.id
    if kind=="struct": return {"type":"struct","nullable":is_nullable,"fields":{k:from_duck_type(v,True) for k,v in t.children}}
    if kind=="list": return {"type":"array","nullable":is_nullable,"items":from_duck_type(t.children[0][1],True)}
    if kind=="decimal":
        children=dict(t.children)
        return {"type":"decimal","nullable":is_nullable,"precision":children["precision"],"scale":children["scale"]}
    names={"bigint":"integer","integer":"integer","smallint":"integer","boolean":"boolean","varchar":"string","date":"date","timestamp":"timestamp"}
    if kind not in names: raise CompileError("UNSUPPORTED_SOURCE_TYPE",str(t))
    return {"type":names[kind],"nullable":is_nullable}

def json_default(x):
    if isinstance(x,Decimal): return str(x)
    if isinstance(x,date): return x.isoformat()
    raise TypeError(type(x).__name__)

def json_text(x):
    return json.dumps(x,sort_keys=True,default=json_default,ensure_ascii=False)

VALUE_TYPE="STRUCT(integer_value BIGINT, decimal_value DECIMAL(28,6), boolean_value BOOLEAN, string_value VARCHAR, date_value DATE, timestamp_value TIMESTAMP)"
VAR_TYPE=f"STRUCT(id VARCHAR, version BIGINT, data_type VARCHAR, dependencies VARCHAR[], value {VALUE_TYPE}, error_code VARCHAR, error_message VARCHAR)[]"
RULE_TYPE="STRUCT(id VARCHAR, version BIGINT, result BOOLEAN, error_code VARCHAR, error_message VARCHAR)[]"

class DuckDBBackend:
    def __init__(self,connection,allowed_tables):
        self.connection=connection
        self.allowed_tables=dict(allowed_tables)
        connection.execute("""CREATE TABLE IF NOT EXISTS rm_runs (
          kind VARCHAR, execution_id VARCHAR, request_hash VARCHAR, status VARCHAR,
          row_count BIGINT, details JSON, PRIMARY KEY(kind,execution_id))""")

    def catalog(self):
        import duckdb
        result={}
        for logical,physical in self.allowed_tables.items():
            rows=self.connection.execute("DESCRIBE "+table_name(physical)).fetchall()
            result[logical]=CatalogTable(physical,{r[0]:from_duck_type(duckdb.sqltype(r[1]),r[2]!="NO") for r in rows})
        return result

    def existing(self,kind,run_id,request_hash):
        row=self.connection.execute("SELECT request_hash,status,row_count,details FROM rm_runs WHERE kind=? AND execution_id=?",[kind,run_id]).fetchone()
        if row:
            if row[0]!=request_hash: raise CompileError("RUN_ID_CONFLICT","Execution ID already binds different inputs/logic")
            return {"execution_id":run_id,"status":row[1],"rows":row[2],"reused":True,"details":json.loads(row[3])}
        return None

    def materialize(self,definition,execution_id,processing_date):
        processing_date=date.fromisoformat(str(processing_date))
        request_hash=canonical_hash({"definition":definition,"date":str(processing_date),"library":__version__})
        old=self.existing("input",execution_id,request_hash)
        if old: return old
        plan=compile_inputs(definition,self.catalog())
        con=self.connection
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute("CREATE OR REPLACE TEMP TABLE rm_input_stage AS "+plan.sql)
            duplicate=con.execute("SELECT client FROM rm_input_stage GROUP BY client HAVING COUNT(*)>1 OR client IS NULL LIMIT 1").fetchone()
            if duplicate: raise EvaluationError("DUPLICATE_CLIENT","Root source has duplicate/null client keys")
            for _,fields in con.execute("SELECT client,fields FROM rm_input_stage").fetchall():
                value_as(fields,definition["output_schema"])
            con.execute(f"""CREATE TABLE IF NOT EXISTS consolidated_inputs(
                execution_id VARCHAR, date DATE, client VARCHAR, version BIGINT, created_by VARCHAR,
                fields {sql_type(definition["output_schema"])},
                PRIMARY KEY(execution_id,date,client,version))""")
            actual=con.execute("DESCRIBE consolidated_inputs").fetchall()[-1][1]
            import duckdb
            if duckdb.sqltype(actual)!=duckdb.sqltype(sql_type(definition["output_schema"])):
                raise CompileError("STORAGE_SCHEMA_MISMATCH","Local consolidated table has another payload schema; use a separate database/migration")
            con.execute("INSERT INTO consolidated_inputs SELECT ?,?,client,?,?,fields FROM rm_input_stage",
                        [execution_id,processing_date,definition["definition_version"],definition["created_by"]])
            count=con.execute("SELECT count(*) FROM rm_input_stage").fetchone()[0]
            details={"definition":definition,"definition_hash":canonical_hash(definition),"library_version":__version__,
                     "sql":plan.sql,"date":str(processing_date),"schema_hash":canonical_hash(definition["output_schema"])}
            con.execute("INSERT INTO rm_runs VALUES ('input',?,?, 'completed',?,?)",[execution_id,request_hash,count,json_text(details)])
            con.execute("COMMIT")
        except Exception as exc:
            con.execute("ROLLBACK")
            if "More than one row returned by a subquery" in str(exc):
                raise EvaluationError("CARDINALITY_VIOLATION","More than one match in declared 1:1 relationship") from None
            raise
        return {"execution_id":execution_id,"status":"completed","rows":count,"reused":False}

    def evaluate(self,document,input_execution_id,evaluation_id,products=None):
        con=self.connection
        run=con.execute("SELECT status,details FROM rm_runs WHERE kind='input' AND execution_id=?",[input_execution_id]).fetchone()
        if not run or run[0]!="completed": raise CompileError("INPUT_NOT_COMPLETED",input_execution_id)
        definition=json.loads(run[1])["definition"]
        plan=EvaluationPlan(document,definition)
        selected=sorted(plan.products) if products is None else sorted(products)
        if not selected or len(set(selected))!=len(selected) or any(p not in plan.products for p in selected):
            raise CompileError("UNKNOWN_PRODUCT","Select existing distinct products")
        request_hash=canonical_hash({"package":document,"input_execution_id":input_execution_id,
                                     "products":selected,"library":__version__})
        old=self.existing("evaluation",evaluation_id,request_hash)
        if old: return old
        con.execute("BEGIN TRANSACTION")
        try:
            con.execute("""CREATE TABLE IF NOT EXISTS evaluations(
              execution_id VARCHAR, client VARCHAR, product VARCHAR, product_version BIGINT, result BOOLEAN,
              error_code VARCHAR,error_message VARCHAR,input_execution_id VARCHAR,
              package_id VARCHAR,package_version BIGINT,PRIMARY KEY(execution_id,client,product))""")
            con.execute(f"""CREATE TABLE IF NOT EXISTS virtual_variables(
              execution_id VARCHAR,client VARCHAR,input_execution_id VARCHAR,variables {VAR_TYPE},
              PRIMARY KEY(execution_id,client))""")
            con.execute(f"""CREATE TABLE IF NOT EXISTS rule_results(
              execution_id VARCHAR,client VARCHAR,input_execution_id VARCHAR,rules {RULE_TYPE},
              PRIMARY KEY(execution_id,client))""")
            rows=con.execute("SELECT client,fields FROM consolidated_inputs WHERE execution_id=? ORDER BY client",[input_execution_id]).fetchall()
            batches=[[],[],[]];errors=0
            def flush():
                if not batches[0]: return
                self._insert_batch("evaluations",batches[0])
                self._insert_batch("virtual_variables",batches[1])
                self._insert_batch("rule_results",batches[2])
                for batch in batches: batch.clear()
            for client,fields in rows:
                result=plan.evaluate_client(fields,selected)
                def err(entry,key): return entry["error"][key] if entry["error"] else None
                for p in result["products"]:
                    errors+=p["error"] is not None
                    batches[0].append((evaluation_id,client,p["id"],p["version"],p["value"],err(p,"code"),err(p,"message"),
                                       input_execution_id,document["definition_id"],document["definition_version"]))
                varlist=[]
                for v in result["variables"]:
                    val={k:None for k in ("integer_value","decimal_value","boolean_value","string_value","date_value","timestamp_value")}
                    kind=v["data_type"]["type"]
                    if kind not in ("integer","decimal","boolean","string","date","timestamp"):
                        raise CompileError("UNSUPPORTED_VARIABLE_TYPE","Local trace supports scalar virtual variables")
                    val[kind+"_value"]=v["value"]
                    varlist.append({"id":v["id"],"version":v["version"],"data_type":json_text(v["data_type"]),
                                    "dependencies":v["dependencies"],"value":val,
                                    "error_code":err(v,"code"),"error_message":err(v,"message")})
                batches[1].append((evaluation_id,client,input_execution_id,varlist))
                batches[2].append((evaluation_id,client,input_execution_id,[
                    {"id":r["id"],"version":r["version"],"result":r["value"],"error_code":err(r,"code"),"error_message":err(r,"message")}
                    for r in result["rules"]]))
                if len(batches[1])>=500: flush()
            flush()
            status="completed_with_errors" if errors else "completed"
            details={"package":document,"package_hash":canonical_hash(document),"input_execution_id":input_execution_id,
                     "products":selected,"product_errors":errors,"library_version":__version__}
            con.execute("INSERT INTO rm_runs VALUES ('evaluation',?,?,?,?,?)",
                        [evaluation_id,request_hash,status,len(rows)*len(selected),json_text(details)])
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK");raise
        return {"execution_id":evaluation_id,"status":status,"rows":len(rows)*len(selected),
                "product_errors":errors,"reused":False}

    def _insert_batch(self, table, rows):
        # Typed bulk ingestion avoids executing an INSERT for each client/trace.
        import tempfile
        from .types import quote
        con=self.connection
        columns=con.execute("DESCRIBE "+quote(table)).fetchall()
        names=[c[0] for c in columns]
        types="{"+", ".join("'"+c[0].replace("'","''")+"': '"+c[1].replace("'","''")+"'" for c in columns)+"}"
        with tempfile.NamedTemporaryFile(mode="w+",suffix=".jsonl",prefix="rule-manager-batch-") as f:
            for row in rows:
                f.write(json_text(dict(zip(names,row)))+"\n")
            f.flush()
            con.execute(f"INSERT INTO {quote(table)} SELECT * FROM read_json(?, columns={types}, format='newline_delimited')",[f.name])

    def export_inputs(self,execution_id,directory):
        """DuckDB has no table partition DDL; persist an execution-partitioned Parquet dataset."""
        from pathlib import Path
        rows=self.connection.execute("SELECT * FROM consolidated_inputs WHERE execution_id=?",[execution_id]).fetchall()
        if not rows: raise CompileError("UNKNOWN_EXECUTION",execution_id)
        # Destination is a trusted adapter argument, never an authored DSL path.
        directory=Path(directory).resolve()
        directory.mkdir(parents=True,exist_ok=True)
        escaped=str(directory).replace("'","''")
        self.connection.execute("CREATE OR REPLACE TEMP TABLE rm_export AS SELECT * FROM consolidated_inputs WHERE execution_id=?",[execution_id])
        self.connection.execute(f"COPY rm_export TO '{escaped}' (FORMAT PARQUET, PARTITION_BY(execution_id), OVERWRITE_OR_IGNORE)")
