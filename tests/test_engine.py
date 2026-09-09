from copy import deepcopy
from decimal import Decimal
import pytest
from rule_manager.engine import EvaluationPlan
from rule_manager.expressions import op,ref,literal,infer,evaluate_expression,TypeEnvironment
from rule_manager.types import BOOL,INT,DECIMAL
from rule_manager.errors import CompileError,EvaluationError

def test_partial_errors_and_all_traces(backend,db,definitions):
    i,e=definitions
    backend.materialize(i,"input","2026-09-09")
    report=backend.evaluate(e,"input","eval")
    assert report["rows"]==60 and report["product_errors"]==1
    rows=dict(db.execute("SELECT product,result FROM evaluations WHERE client='C000000'").fetchall())
    assert rows["basic_account"] is True
    assert rows["demo_credit"] is None
    rules=db.execute("SELECT rules FROM rule_results WHERE client='C000000'").fetchone()[0]
    assert len(rules)==4
    assert next(r for r in rules if r["id"]=="affordability")["error_code"]=="DEPENDENCY_ERROR"
    variables=db.execute("SELECT variables FROM virtual_variables WHERE client='C000000'").fetchone()[0]
    assert next(v for v in variables if v["id"]=="debt_ratio")["error_code"]=="DIVISION_BY_ZERO"
    assert db.execute("SELECT count(*) FROM virtual_variables").fetchone()[0]==20
    assert db.execute("SELECT count(*) FROM rule_results").fetchone()[0]==20
    assert backend.evaluate(e,"input","eval")["reused"]
    assert db.execute("SELECT count(*) FROM evaluations").fetchone()[0]==60

def test_rule_error_cannot_be_hidden_by_or(backend,db,definitions):
    i,e=deepcopy(definitions)
    e["products"][1]["expression"]=op("or",ref("rule","adult"),ref("rule","affordability"))
    backend.materialize(i,"i","2026-09-09");backend.evaluate(e,"i","e")
    assert db.execute("SELECT result FROM evaluations WHERE client='C000000' AND product='demo_credit'").fetchone()[0] is None

def test_selected_products_compute_only_reachable_variables(backend,db,definitions):
    i,e=definitions
    backend.materialize(i,"i","2026-09-09")
    backend.evaluate(e,"i","e",["basic_account"])
    assert db.execute("SELECT variables FROM virtual_variables LIMIT 1").fetchone()[0]==[]
    assert db.execute("SELECT count(*) FROM evaluations").fetchone()[0]==20

def test_immutable_run_binding(backend,definitions):
    i,e=deepcopy(definitions);backend.materialize(i,"i","2026-09-09");backend.evaluate(e,"i","e")
    e["constants"]["minimum_age"]["value"]=30
    with pytest.raises(CompileError,match="RUN_ID_CONFLICT"): backend.evaluate(e,"i","e")

@pytest.mark.parametrize("operator,expected",[
 ("sum",0),("count",0),("min",None),("max",None),("mean",None),("exists",False),("all",True)
])
def test_empty_array_semantics(operator,expected):
    expr=op(operator,ref("input","accounts"),*( [op("gt",ref("item","balance"),literal(0))] if operator in ("exists","all") else []),
            **({"path":["balance"]} if operator in ("sum","min","max","mean") else {}))
    assert evaluate_expression(expr,{"input":{"accounts":[]}})==expected

def test_null_elements_are_skipped_by_numeric_aggregates():
    expr=op("mean",ref("input","values"))
    assert evaluate_expression(expr,{"input":{"values":[None,Decimal("2"),Decimal("4")]}})==Decimal("3.000000")
    assert evaluate_expression(expr,{"input":{"values":[None]}}) is None

def test_decimal_rounding_and_overflow():
    from rule_manager.types import value_as
    assert evaluate_expression(op("div",literal(1),literal(3)),{})==Decimal("0.333333")
    with pytest.raises(EvaluationError,match="overflow"): value_as(2**63,INT)

def test_uncompleted_input_is_rejected(backend,definitions):
    with pytest.raises(CompileError,match="INPUT_NOT_COMPLETED"): backend.evaluate(definitions[1],"unknown","e")

def test_invalid_schema_extra_fields(definitions):
    i,e=deepcopy(definitions);e["execute_python"]="bad"
    with pytest.raises(CompileError,match="INVALID_SCHEMA"): EvaluationPlan(e,i)
