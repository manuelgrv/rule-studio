from copy import deepcopy
from decimal import Decimal
import pytest
from rule_manager.inputs import compile_inputs
from rule_manager.errors import CompileError,EvaluationError
from rule_manager.synthetic import generate_banking_data

def test_native_struct_lists_chained_joins_and_no_cartesian(backend,db,definitions):
    inputs,_=definitions
    backend.materialize(inputs,"i1","2026-09-09")
    assert db.execute("SELECT count(*) FROM consolidated_inputs").fetchone()[0]==20
    fields=db.execute("SELECT fields FROM consolidated_inputs WHERE client='C000002'").fetchone()[0]
    assert len(fields["accounts"])==2
    assert len(fields["loans"])==3
    assert len(fields["accounts"][0]["movements"])==3
    assert isinstance(fields["accounts"][0]["balance"],Decimal)
    assert db.execute("SELECT fields.accounts FROM consolidated_inputs WHERE client='C000001'").fetchone()[0]==[]
    spouse=db.execute("SELECT fields.spouse FROM consolidated_inputs WHERE client='C000000'").fetchone()[0]
    assert spouse["financial"]["income"] is not None
    assert db.execute("SELECT fields.spouse FROM consolidated_inputs WHERE client='C000003'").fetchone()[0] is None

def test_input_retries_and_new_same_day_runs(backend,db,definitions):
    i,_=definitions
    backend.materialize(i,"first","2026-09-09")
    assert backend.materialize(i,"first","2026-09-09")["reused"]
    backend.materialize(i,"second","2026-09-09")
    assert db.execute("SELECT count(*) FROM consolidated_inputs").fetchone()[0]==40
    with pytest.raises(CompileError,match="RUN_ID_CONFLICT"): backend.materialize(i,"first","2026-09-10")

def test_cardinality_error_rolls_back(backend,db,definitions):
    i,_=definitions
    db.execute("INSERT INTO finances SELECT * FROM finances WHERE client_id='C000000'")
    with pytest.raises(EvaluationError,match="More than one"): backend.materialize(i,"bad","2026-09-09")
    assert db.execute("SELECT count(*) FROM rm_runs").fetchone()[0]==0

@pytest.mark.parametrize("change",["field","table","type","cycle","cardinality"])
def test_compile_rejects_bad_mapping(backend,definitions,change):
    i,_=deepcopy(definitions)
    if change=="field": i["mappings"]["age"]["ref"]["field"]="secret"
    if change=="table": i["sources"][0]["table_ref"]="unlisted"
    if change=="type": i["output_schema"]["fields"]["age"]["type"]="string"
    if change=="cycle": i["joins"][0]["parent"]="f"
    if change=="cardinality": i["joins"][3]["cardinality"]="one"
    with pytest.raises(CompileError): compile_inputs(i,backend.catalog())

def test_catalog_drift(backend,db,definitions):
    i,_=definitions
    db.execute("ALTER TABLE clients ALTER age TYPE VARCHAR")
    with pytest.raises(CompileError,match="CATALOG_DRIFT"): compile_inputs(i,backend.catalog())

def test_export_execution_partition(backend,definitions,tmp_path):
    backend.materialize(definitions[0],"partition-test","2026-09-09")
    backend.export_inputs("partition-test",tmp_path/"inputs")
    assert list((tmp_path/"inputs"/"execution_id=partition-test").glob("*.parquet"))

def test_generator_never_overwrites(db):
    with pytest.raises(CompileError,match="FIXTURE_EXISTS"): generate_banking_data(db,20)

def test_nonnullable_source_data(db,backend,definitions):
    i,_=deepcopy(definitions)
    db.execute("DELETE FROM finances WHERE client_id='C000000'")
    backend.materialize(i,"missing-finance","2026-09-09")
    assert db.execute("SELECT fields.financial FROM consolidated_inputs WHERE client='C000000'").fetchone()[0] is None

def test_one_to_one_scalar_and_required_object(backend,db,definitions):
    i,_=deepcopy(definitions)
    i["mappings"]["income_scalar"]={"ref":{"source":"f","field":"income"},"join":"financial"}
    i["output_schema"]["fields"]["income_scalar"]={"type":"decimal","precision":18,"scale":2,"nullable":True}
    i["output_schema"]["fields"]["financial"]["nullable"]=False
    backend.materialize(i,"scalar","2026-09-09")
    assert db.execute("SELECT fields.income_scalar FROM consolidated_inputs WHERE client='C000000'").fetchone()[0]==Decimal("0.00")
    db.execute("DELETE FROM finances WHERE client_id='C000000'")
    with pytest.raises(EvaluationError,match="Non-null"): backend.materialize(i,"missing","2026-09-09")
    assert db.execute("SELECT count(*) FROM consolidated_inputs WHERE execution_id='missing'").fetchone()[0]==0

def test_export_retry_does_not_duplicate(backend,db,definitions,tmp_path):
    backend.materialize(definitions[0],"export-run","2026-09-09")
    target=tmp_path/"inputs"
    backend.export_inputs("export-run",target)
    backend.export_inputs("export-run",target)
    assert db.execute("SELECT count(*) FROM read_parquet(?)",[str(target/"**/*.parquet")]).fetchone()[0]==20
