"""Machine-readable closed schemas; semantic checks live in validation.py."""
import json
from importlib.resources import files
from jsonschema import Draft202012Validator
from .errors import CompileError

def schema(kind):
    return json.loads(files("rule_manager").joinpath("schemas", kind + ".schema.json").read_text())

def validate_document(document, kind):
    errors = sorted(Draft202012Validator(schema(kind)).iter_errors(document), key=lambda e:str(e.path))
    if errors:
        e = errors[0]
        raise CompileError("INVALID_SCHEMA", e.message, "$." + ".".join(map(str,e.absolute_path)))
