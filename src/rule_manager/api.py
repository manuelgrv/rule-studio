"""Small shared API for a future web backend; returns JSON-serializable artifacts."""
from copy import deepcopy
from dataclasses import dataclass,asdict
import hashlib
import json
from jsonschema import Draft202012Validator,ValidationError
from . import __version__
from .authoring import compile_python,compile_sql
from .expressions import infer
from .schemas import schema
from .types import BOOL
from .validation import bounded
from .errors import CompileError

@dataclass(frozen=True)
class RuleCompilation:
    expression: dict
    language: str
    source: str
    source_hash: str
    compiler_version: str

    def to_dict(self):
        return asdict(self)

def compile_rule(source,language,environment):
    if language=="visual":
        if not isinstance(source,dict): raise CompileError("INVALID_SCHEMA","Visual source must be an expression tree")
        expression=deepcopy(source)
        text=json.dumps(source,sort_keys=True,separators=(",",":"))
    elif language in ("python","sql"):
        if not isinstance(source,str): raise CompileError("INVALID_SOURCE","Text source required")
        text=source
        expression=(compile_python if language=="python" else compile_sql)(source,environment)
    else:
        raise CompileError("UNSUPPORTED_LANGUAGE",language)
    bounded(expression)
    definitions=schema("evaluations")["$defs"]
    try:
        Draft202012Validator({"$ref":"#/$defs/expression","$defs":definitions}).validate(expression)
    except ValidationError as e:
        raise CompileError("INVALID_SCHEMA",e.message) from None
    if infer(expression,environment)!=BOOL:
        raise CompileError("NON_BOOLEAN_RETURN","Rule must return non-null Boolean")
    return RuleCompilation(expression,language,text,hashlib.sha256(text.encode()).hexdigest(),__version__)
