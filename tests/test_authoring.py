from copy import deepcopy
from decimal import Decimal
import pytest
from rule_manager.authoring import compile_python,compile_sql
from rule_manager.expressions import ref,op,literal,TypeEnvironment,evaluate_expression
from rule_manager.types import BOOL,INT,DECIMAL,nullable
from rule_manager.errors import CompileError
from rule_manager.examples import PYTHON_RULE,SQL_RULE
from rule_manager.validation import validate_evaluations

def test_three_authoring_modes_identical(env,definitions):
    visual=definitions[1]["rules"][0]["expression"]
    assert compile_python(PYTHON_RULE,env)==compile_sql(SQL_RULE,env)==visual

@pytest.mark.parametrize("python,sql",[
 ('return inputs["age"] >= 18 and inputs["age"] < 80','inputs.age >= 18 AND inputs.age < 80'),
 ('return not (inputs["age"] < 18)','NOT (inputs.age < 18)'),
 ('return exists(inputs["accounts"], lambda item: item["balance"] > 0)',"DSL_EXISTS(inputs.accounts, item.balance > 0)"),
 ('return forall(inputs["accounts"], lambda item: item["balance"] >= 0)',"DSL_ALL(inputs.accounts, item.balance >= 0)"),
 ('return count_items(inputs["accounts"]) > 0',"DSL_COUNT(inputs.accounts) > 0"),
 ('return sum_values(inputs["accounts"], "balance") > 0',"DSL_SUM(inputs.accounts, 'balance') > 0"),
 ('return coalesce(variables["income"], constants["zero_money"]) > 0',"COALESCE(variables.income, constants.zero_money) > 0"),
 ('return inputs["spouse"] is None',"inputs.spouse IS NULL"),
 ('return inputs["spouse"] is not None',"inputs.spouse IS NOT NULL"),
 ('return True if inputs["age"] >= 18 else False',"CASE WHEN inputs.age >= 18 THEN TRUE ELSE FALSE END")
])
def test_equivalent_expressions(env,python,sql):
    assert compile_python("def rule(inputs, variables, constants) -> bool:\n    "+python,env)==compile_sql(sql,env)

def test_local_assignment_and_branches(env):
    source='''def rule(inputs) -> bool:
    adult = inputs["age"] >= 18
    if adult:
        return True
    else:
        return False
'''
    assert compile_python(source,env)==op("let",op("gte",ref("input","age"),literal(18)),op("if",ref("local","adult"),literal(True),literal(False)),name="adult")

def test_branch_with_continuation(env):
    source='''def rule(inputs) -> bool:
    if inputs["age"] > 50:
        return True
    return inputs["age"] >= 18
'''
    compile_python(source,env)

@pytest.mark.parametrize("source",[
 'import os\ndef rule(inputs) -> bool:\n    return True',
 'def rule(inputs) -> bool:\n    return 1',
 'def rule(inputs) -> bool:\n    return None',
 'def rule(inputs) -> bool:\n    if inputs["age"] > 20:\n        return True',
 'def rule(inputs) -> bool:\n    return open("/tmp/should-not-exist").read()',
 'def rule(inputs) -> bool:\n    return eval("True")',
 'def rule(inputs) -> bool:\n    return inputs["missing"] > 1',
 'def rule(inputs) -> bool:\n    return inputs["financial"]["income"] > 0',
 'def rule(inputs) -> bool:\n    for x in []:\n        return True',
 'def rule(inputs) -> bool:\n    return variables["income"] > 0',
 'def rule(inputs) -> bool:\n    return inputs.__class__ == "x"',
 'def rule(inputs) -> bool:\n    return (lambda: True)()',
 '@decorator\ndef rule(inputs) -> bool:\n    return True',
 'def rule(inputs=True) -> bool:\n    return True',
 'def rule(inputs) -> bool:\n    value = 1\n    value = 2\n    return True'
])
def test_rejects_unsafe_untyped_or_incomplete_python(env,source):
    with pytest.raises(CompileError) as e: compile_python(source,env)
    assert e.value.diagnostic.code

@pytest.mark.parametrize("source",[
 "SELECT * FROM clients","SELECT TRUE FROM read_csv('/tmp/no')",
 "DROP TABLE clients","SELECT TRUE; SELECT FALSE","random() > 0.5",
 "inputs.missing > 0","inputs.financial.income > 0",
 "1","NULL","SELECT TRUE UNION SELECT FALSE",
 "CASE WHEN inputs.age > 18 THEN TRUE END",
])
def test_rejects_sql(env,source):
    with pytest.raises(CompileError): compile_sql(source,env)

def test_diagnostic_location(env):
    with pytest.raises(CompileError) as e: compile_python('def r(inputs) -> bool:\n    return open("x")',env)
    assert e.value.diagnostic.line==2

def test_sql_select_expression(env):
    assert compile_sql("SELECT inputs.age >= 18",env)==compile_sql("inputs.age >= 18",env)

def test_cyclic_variables(definitions):
    i,e=deepcopy(definitions)
    e["variables"][0]["expression"]=ref("variable","debt")
    e["variables"][1]["expression"]=ref("variable","income")
    with pytest.raises(CompileError,match="CYCLIC_DEPENDENCY"): validate_evaluations(e,i)

def test_wrong_input_version(definitions):
    i,e=deepcopy(definitions);e["input_contract"]["definition_version"]=2
    with pytest.raises(CompileError,match="INPUT_CONTRACT_MISMATCH"): validate_evaluations(e,i)

def test_product_cannot_score(definitions):
    i,e=deepcopy(definitions)
    e["products"][0]["expression"]=op("gt",literal(1),literal(0))
    with pytest.raises(CompileError,match="INVALID_PRODUCT"): validate_evaluations(e,i)

def test_nullable_final_return_rejected(env):
    source='def r(inputs) -> bool:\n    return mean_value(inputs["accounts"], "balance") > 0'
    with pytest.raises(CompileError,match="NON_BOOLEAN_RETURN"): compile_python(source,env)

@pytest.mark.parametrize("expr",['-"text"', '-True'])
def test_unary_minus_does_not_coerce_non_numbers(env,expr):
    with pytest.raises(CompileError): compile_python("def r(inputs) -> bool:\n    return "+expr+" > 0",env)

def test_source_depth_limit(env):
    with pytest.raises(CompileError,match="COMPLEXITY_LIMIT"):
        compile_python("def r(inputs) -> bool:\n    return "+"not "*70+"True",env)

def test_unreachable_import_still_rejected(env):
    source="""def r(inputs) -> bool:
    if inputs["age"] > 18:
        return True
    else:
        return False
    import os
"""
    with pytest.raises(CompileError): compile_python(source,env)

def test_unused_assignment_is_still_typechecked(env):
    with pytest.raises(CompileError,match="UNKNOWN_FIELD"):
        compile_python('def r(inputs) -> bool:\n    unused = inputs["missing"]\n    return True',env)

def test_unused_local_error_is_not_discarded(env):
    from rule_manager.errors import EvaluationError
    tree=compile_python('def r(inputs) -> bool:\n    unused = 1 / 0\n    return True',env)
    with pytest.raises(EvaluationError,match="Denominator"):
        evaluate_expression(tree,{"input":{"age":40}})

def test_local_references_do_not_expand_exponentially(env):
    source="def r(inputs) -> bool:\n    x0 = 1\n"
    for i in range(1,15): source+=f"    x{i} = x{i-1} + x{i-1}\n"
    source+="    return x14 > 0"
    import json
    tree=compile_python(source,env)
    assert len(json.dumps(tree))<10000
    assert evaluate_expression(tree,{}) is True
