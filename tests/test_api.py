from rule_manager.api import compile_rule
from rule_manager.examples import PYTHON_RULE,SQL_RULE
from rule_manager.errors import CompileError
import pytest

def test_shared_api_preserves_source_provenance(env,definitions):
    visual=definitions[1]["rules"][0]["expression"]
    artifacts=[compile_rule(s,l,env) for s,l in [(visual,"visual"),(PYTHON_RULE,"python"),(SQL_RULE,"sql")]]
    assert artifacts[0].expression==artifacts[1].expression==artifacts[2].expression
    assert artifacts[1].source==PYTHON_RULE
    assert len(artifacts[1].source_hash)==64
    assert artifacts[0].to_dict()["compiler_version"]

def test_visual_extra_fields_fail(env,definitions):
    bad={**definitions[1]["rules"][0]["expression"],"arbitrary_code":"hello"}
    with pytest.raises(CompileError): compile_rule(bad,"visual",env)
