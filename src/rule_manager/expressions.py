from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from .errors import CompileError, EvaluationError
from .types import BOOL, INT, DECIMAL, numeric, nullable, path_type, compatible, value_as

OPS = {
    "add":2,"sub":2,"mul":2,"div":2,
    "eq":2,"ne":2,"gt":2,"gte":2,"lt":2,"lte":2,
    "not":1,"is_null":1,"coalesce":2,"if":3,
    "sum":1,"count":1,"min":1,"max":1,"mean":1,"exists":2,"all":2,
    "and":None,"or":None,"let":2,
}

def ref(scope, *path):
    return {"ref":{"scope":scope,"path":list(path)}}

def literal(value):
    if value is None:
        raise CompileError("UNTYPED_NULL", "Use is_null or coalesce; untyped null literals are not supported")
    if type(value) is bool: t=BOOL
    elif type(value) is int: t=INT
    elif isinstance(value, (Decimal,float)):
        t=DECIMAL; value=str(value)
    elif isinstance(value,str): t={"type":"string","nullable":False}
    else: raise CompileError("UNSUPPORTED_LITERAL", str(type(value)))
    return {"literal":{"value":value,"data_type":deepcopy(t)}}

def op(operator, *args, **extra):
    return {"op":operator,"args":list(args),**extra}

def dependencies(expr, scope):
    result=set()
    def walk(node):
        if "ref" in node and node["ref"]["scope"]==scope:
            result.add(node["ref"]["path"][0])
        for arg in node.get("args",[]): walk(arg)
    walk(expr)
    return result

class TypeEnvironment:
    def __init__(self, inputs, variables=None, constants=None, rules=None, item=None, locals_=None):
        self.inputs=inputs
        self.variables=variables or {}
        self.constants=constants or {}
        self.rules=rules or {}
        self.item=item
        self.locals=locals_ or {}

    def resolve(self, reference):
        scope,path=reference["scope"],reference["path"]
        if scope in ("input","item"):
            root=self.inputs if scope=="input" else self.item
            if root is None: raise CompileError("UNKNOWN_FIELD", "item is only valid in array predicates")
            return path_type(root,path)
        mapping={"variable":self.variables,"constant":self.constants,"rule":self.rules,"local":self.locals}[scope]
        if path[0] not in mapping:
            raise CompileError("UNKNOWN_FIELD", f"{scope}.{'.'.join(path)}")
        return path_type(mapping[path[0]],path[1:])

def infer(expr, env):
    if "ref" in expr: return env.resolve(expr["ref"])
    if "literal" in expr:
        lit=expr["literal"]
        try: value_as(decode_literal(lit),lit["data_type"])
        except (EvaluationError, ValueError) as e: raise CompileError(getattr(e,"code","INVALID_LITERAL"),str(e)) from None
        return lit["data_type"]
    name,args=expr["op"],expr["args"]
    if name not in OPS:
        raise CompileError("UNKNOWN_OPERATOR",name)
    n=OPS[name]
    if (n is not None and len(args)!=n) or (n is None and len(args)<2):
        raise CompileError("ARITY",f"{name}: invalid number of arguments")
    if expr.get("path") is not None and name not in ("sum","min","max","mean","count"):
        raise CompileError("INVALID_OPERATOR_PATH",name)
    if name=="let":
        if not expr.get("name") or expr["name"] in env.locals:
            raise CompileError("INVALID_LOCAL","let requires a new local name")
        value_type=infer(args[0],env)
        child=TypeEnvironment(env.inputs,env.variables,env.constants,env.rules,env.item,{**env.locals,expr["name"]:value_type})
        return infer(args[1],child)
    if "name" in expr: raise CompileError("INVALID_LOCAL","name is only valid on let")
    if name in ("exists","all"):
        arr=infer(args[0],env)
        if arr["type"]!="array": raise CompileError("TYPE_MISMATCH",name+" requires array")
        child=TypeEnvironment(env.inputs,env.variables,env.constants,env.rules,arr["items"],env.locals)
        pred=infer(args[1],child)
        if pred!=BOOL: raise CompileError("TYPE_MISMATCH","Array predicate must be non-null Boolean")
        return nullable(BOOL,arr["nullable"])
    ts=[infer(a,env) for a in args]
    null=any(t["nullable"] for t in ts)
    if name in ("add","sub","mul","div"):
        if not all(numeric(t) for t in ts): raise CompileError("TYPE_MISMATCH","Arithmetic needs numbers")
        return nullable(DECIMAL if name=="div" or any(t["type"]=="decimal" for t in ts) else INT,null)
    if name in ("eq","ne","gt","gte","lt","lte"):
        if not (all(numeric(t) for t in ts) or (ts[0]["type"]==ts[1]["type"] and ts[0]["type"] in ("boolean","string","date","timestamp"))):
            raise CompileError("TYPE_MISMATCH","Incompatible comparison")
        if name not in ("eq","ne") and ts[0]["type"]=="boolean":
            raise CompileError("TYPE_MISMATCH","Boolean ordering is not supported")
        return nullable(BOOL,null)
    if name in ("and","or","not"):
        if any(t["type"]!="boolean" for t in ts): raise CompileError("TYPE_MISMATCH","Logic needs Booleans")
        return nullable(BOOL,null)
    if name=="is_null": return deepcopy(BOOL)
    if name=="coalesce":
        if not compatible(ts[0],ts[1],ignore_null=True):
            raise CompileError("TYPE_MISMATCH","coalesce requires the same exact type")
        return nullable(ts[0],ts[0]["nullable"] and ts[1]["nullable"])
    if name=="if":
        if ts[0]!=BOOL or not compatible(ts[1],ts[2],ignore_null=True):
            raise CompileError("TYPE_MISMATCH","if requires a non-null condition and matching branches")
        return nullable(ts[1],ts[1]["nullable"] or ts[2]["nullable"])
    if name in ("sum","count","min","max","mean"):
        arr=ts[0]
        if arr["type"]!="array": raise CompileError("TYPE_MISMATCH",name+" requires array")
        element=path_type(arr["items"],expr.get("path",[]))
        if name=="count":
            if expr.get("path"): raise CompileError("INVALID_OPERATOR_PATH","count counts all elements")
            return nullable(INT,arr["nullable"])
        if not numeric(element): raise CompileError("TYPE_MISMATCH",name+" requires numeric elements/path")
        # Null elements are skipped; all-null numeric input has the same aggregate value as [].
        return nullable(DECIMAL if name=="mean" or element["type"]=="decimal" else INT,
                        arr["nullable"] or name in ("min","max","mean"))
    raise CompileError("UNKNOWN_OPERATOR",name)

def decode_literal(lit):
    value,t=lit["value"],lit["data_type"]
    if value is None: return None
    if t["type"]=="decimal": return Decimal(value)
    if t["type"]=="date": return date.fromisoformat(value)
    if t["type"]=="timestamp": return datetime.fromisoformat(value)
    return value

def lookup(value,path):
    for key in path:
        if value is None: return None
        if not isinstance(value,dict) or key not in value:
            raise EvaluationError("MISSING_FIELD",".".join(path))
        value=value[key]
    return value

def evaluate_expression(expr, context):
    """Reference interpreter. No eval/exec and no execution of authoring source."""
    if "literal" in expr: return decode_literal(expr["literal"])
    if "ref" in expr:
        r=expr["ref"]
        if r["scope"] in ("variable","rule"):
            dep=context[r["scope"]][r["path"][0]]
            if dep["error"]:
                raise EvaluationError("DEPENDENCY_ERROR",f'{r["scope"]}.{r["path"][0]}: {dep["error"]["code"]}')
            return lookup(dep["value"],r["path"][1:])
        return lookup(context[r["scope"]],r["path"])
    name,args=expr["op"],expr["args"]
    if name=="let":
        value=evaluate_expression(args[0],context)
        return evaluate_expression(args[1],{**context,"local":{**context.get("local",{}),expr["name"]:value}})
    if name=="if":
        return evaluate_expression(args[1] if evaluate_expression(args[0],context) else args[2],context)
    if name=="coalesce":
        v=evaluate_expression(args[0],context)
        return v if v is not None else evaluate_expression(args[1],context)
    if name in ("exists","all"):
        arr=evaluate_expression(args[0],context)
        if arr is None: return None
        values=[evaluate_expression(args[1],{**context,"item":v}) for v in arr]
        if any(v is None for v in values):
            raise EvaluationError("NULL_PREDICATE","Array predicate produced null")
        return any(values) if name=="exists" else all(values)
    values=[evaluate_expression(a,context) for a in args]
    if name=="is_null": return values[0] is None
    if any(v is None for v in values): return None
    if name in ("sum","count","min","max","mean"):
        arr=values[0]
        if name=="count": return len(arr)
        seq=[lookup(x,expr.get("path",[])) for x in arr]
        seq=[x for x in seq if x is not None]
        if name=="sum":
            result=sum(seq)
            return rounded(result) if isinstance(result,Decimal) else value_as(result,INT)
        if not seq: return None
        if name=="min": return min(seq)
        if name=="max": return max(seq)
        with localcontext() as ctx:
            ctx.prec=80
            return rounded(sum(Decimal(x) for x in seq)/len(seq))
    if name=="and": return all(values)
    if name=="or": return any(values)
    if name=="not": return not values[0]
    a,b=values
    if name=="eq": return a==b
    if name=="ne": return a!=b
    if name=="gt": return a>b
    if name=="gte": return a>=b
    if name=="lt": return a<b
    if name=="lte": return a<=b
    with localcontext() as ctx:
        ctx.prec=80
        if name=="div":
            if b==0: raise EvaluationError("DIVISION_BY_ZERO","Denominator is zero")
            return rounded(Decimal(a)/Decimal(b))
        result={"add":lambda:a+b,"sub":lambda:a-b,"mul":lambda:a*b}[name]()
        return rounded(result) if isinstance(result,Decimal) else value_as(result,INT)

def rounded(value):
    return value_as(value.quantize(Decimal("0.000001"),rounding=ROUND_HALF_EVEN),DECIMAL)
