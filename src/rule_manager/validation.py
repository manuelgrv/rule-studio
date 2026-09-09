import hashlib
import json
from copy import deepcopy
from .schemas import validate_document
from .errors import CompileError, EvaluationError
from .types import BOOL, compatible
from .expressions import TypeEnvironment, infer, dependencies, decode_literal
from .types import value_as

def canonical_hash(document):
    return hashlib.sha256(json.dumps(document,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def bounded(document):
    stack=[(document,0)]; count=0
    while stack:
        node,depth=stack.pop();count+=1
        if depth>60 or count>20000:
            raise CompileError("COMPLEXITY_LIMIT","Document exceeds depth/node limits")
        if isinstance(node,dict):
            stack.extend((v,depth+1) for v in node.values())
            if node.get("type")=="decimal" and node.get("scale",0)>node.get("precision",28):
                raise CompileError("TYPE_MISMATCH","Decimal scale exceeds precision")
        elif isinstance(node,list):
            stack.extend((v,depth+1) for v in node)

def unique(entries):
    result={}
    for entry in entries:
        if entry["id"] in result: raise CompileError("DUPLICATE_ID",entry["id"])
        result[entry["id"]]=entry
    return result

def topological(entries,scope):
    mapping=unique(entries); result=[]; visiting=set(); done=set()
    def visit(name):
        if name in done: return
        if name in visiting: raise CompileError("CYCLIC_DEPENDENCY",name)
        if name not in mapping: raise CompileError("UNKNOWN_FIELD",name)
        visiting.add(name)
        for dep in sorted(dependencies(mapping[name]["expression"],scope)): visit(dep)
        visiting.remove(name);done.add(name);result.append(mapping[name])
    for name in mapping: visit(name)
    return result

def validate_inputs(document):
    bounded(document); validate_document(document,"inputs")
    if document["output_schema"]["type"]!="struct" or document["output_schema"]["nullable"]:
        raise CompileError("TYPE_MISMATCH","Root output must be non-null struct")
    return deepcopy(document)

def validate_evaluations(document, input_definition):
    bounded(document);validate_document(document,"evaluations")
    contract=document["input_contract"]
    if (contract["definition_id"]!=input_definition["definition_id"]
        or contract["definition_version"]!=input_definition["definition_version"]
        or contract["schema_hash"]!=canonical_hash(input_definition["output_schema"])):
        raise CompileError("INPUT_CONTRACT_MISMATCH","Input definition/version/schema hash differ")
    constants={}
    for key,lit in document["constants"].items():
        try:
            value_as(decode_literal(lit),lit["data_type"])
        except (EvaluationError, ValueError) as e:
            raise CompileError("INVALID_CONSTANT",str(e)) from None
        constants[key]=lit["data_type"]
    env=TypeEnvironment(input_definition["output_schema"],constants=constants)
    variables=topological(document["variables"],"variable")
    for entry in variables:
        if entry["data_type"]["type"] in ("array","struct"):
            raise CompileError("UNSUPPORTED_VARIABLE_TYPE","Virtual variables are scalar; input arrays remain available to operators")
        if dependencies(entry["expression"],"rule"):
            raise CompileError("INVALID_DEPENDENCY","Variables cannot depend on rules")
        inferred=infer(entry["expression"],env)
        if not compatible(inferred,entry["data_type"]):
            raise CompileError("TYPE_MISMATCH",f'Variable {entry["id"]}: inferred {inferred}, declared {entry["data_type"]}')
        env.variables[entry["id"]]=inferred
    rules=unique(document["rules"])
    for entry in rules.values():
        if dependencies(entry["expression"],"rule"):
            raise CompileError("INVALID_DEPENDENCY","Only products compose rules")
        if entry["data_type"]!=BOOL or infer(entry["expression"],env)!=BOOL:
            raise CompileError("NON_BOOLEAN_RETURN",f'Rule {entry["id"]} must produce a non-null Boolean')
    env.rules={name:BOOL for name in rules}
    unique(document["products"])
    def product_expr(expr):
        if "ref" in expr:
            if expr["ref"]["scope"]!="rule" or len(expr["ref"]["path"])!=1:
                raise CompileError("INVALID_PRODUCT","Products reference rules only")
        elif expr.get("op") in ("and","or","not"):
            for arg in expr["args"]: product_expr(arg)
        else: raise CompileError("INVALID_PRODUCT","Only rule references and AND/OR/NOT")
    for entry in document["products"]:
        product_expr(entry["expression"])
        if infer(entry["expression"],env)!=BOOL:
            raise CompileError("NON_BOOLEAN_RETURN",entry["id"])
    return deepcopy(variables),env
