from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
from .errors import CompileError, EvaluationError

DECIMAL = {"type": "decimal", "precision": 28, "scale": 6, "nullable": False}
BOOL = {"type": "boolean", "nullable": False}
INT = {"type": "integer", "nullable": False}

def nullable(t, value=True):
    return {**t, "nullable": value}

def compatible(a, b, ignore_null=False):
    aa, bb = deepcopy(a), deepcopy(b)
    if ignore_null:
        aa["nullable"] = bb["nullable"] = False
    return aa == bb

def path_type(t, path):
    for key in path:
        if t["type"] != "struct" or key not in t["fields"]:
            raise CompileError("UNKNOWN_FIELD", f"Unknown field path: {'.'.join(path)}")
        parent_null = t["nullable"]
        t = nullable(t["fields"][key], parent_null or t["fields"][key]["nullable"])
    return t

def numeric(t):
    return t["type"] in ("integer", "decimal")

def sql_type(t):
    kind = t["type"]
    if kind == "struct":
        return "STRUCT(" + ", ".join(f'{quote(k)} {sql_type(v)}' for k,v in t["fields"].items()) + ")"
    if kind == "array":
        return sql_type(t["items"]) + "[]"
    if kind == "decimal":
        return f'DECIMAL({t["precision"]},{t["scale"]})'
    return {"integer":"BIGINT", "boolean":"BOOLEAN", "string":"VARCHAR", "date":"DATE", "timestamp":"TIMESTAMP"}[kind]

def quote(identifier):
    return '"' + identifier.replace('"', '""') + '"'

def value_as(value, t, path="$"):
    """Strict output validation, including descendants of STRUCT/LIST values."""
    if value is None:
        if not t["nullable"]:
            raise EvaluationError("NULL_VALUE", f"Non-null field missing at {path}")
        return None
    kind = t["type"]
    if kind == "struct":
        if not isinstance(value, dict) or set(value) != set(t["fields"]):
            raise EvaluationError("TYPE_MISMATCH", f"Invalid struct at {path}")
        return {k:value_as(value[k], typ, f"{path}.{k}") for k,typ in t["fields"].items()}
    if kind == "array":
        if not isinstance(value, list):
            raise EvaluationError("TYPE_MISMATCH", f"Expected array at {path}")
        return [value_as(v, t["items"], f"{path}[{i}]") for i,v in enumerate(value)]
    if kind == "decimal":
        if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
            raise EvaluationError("TYPE_MISMATCH", f"Expected exact decimal at {path}")
        try:
            with localcontext() as ctx:
                ctx.prec = 80
                result = Decimal(value)
                if not result.is_finite():
                    raise InvalidOperation
                rounded = result.quantize(Decimal(1).scaleb(-t["scale"]), rounding=ROUND_HALF_EVEN)
                if rounded != result:
                    raise EvaluationError("PRECISION_LOSS", f"Implicit rounding at {path}")
                if abs(rounded) >= Decimal(10) ** (t["precision"]-t["scale"]):
                    raise EvaluationError("NUMERIC_OVERFLOW", f"Decimal overflow at {path}")
                return rounded
        except (InvalidOperation, ValueError):
            raise EvaluationError("TYPE_MISMATCH", f"Invalid decimal at {path}") from None
    valid = {"integer":type(value) is int, "boolean":type(value) is bool,
             "string":isinstance(value,str), "date":type(value) is date,
             "timestamp":type(value) is datetime}[kind]
    if not valid:
        raise EvaluationError("TYPE_MISMATCH", f"Expected {kind} at {path}")
    if kind == "integer" and not -(2**63) <= value < 2**63:
        raise EvaluationError("NUMERIC_OVERFLOW", f"Integer overflow at {path}")
    return value
