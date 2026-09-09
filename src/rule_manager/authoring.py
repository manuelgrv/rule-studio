"""Closed Python AST and SQLGlot frontends. Neither executes source code."""
import ast
from copy import deepcopy
from decimal import Decimal
import sqlglot
from sqlglot import exp
from .errors import CompileError
from .expressions import literal, ref, op, infer
from .types import BOOL

SCOPES={"inputs":"input","variables":"variable","constants":"constant","item":"item"}
CALLS={"sum_values":"sum","count_items":"count","min_value":"min","max_value":"max",
       "mean_value":"mean","exists":"exists","forall":"all","coalesce":"coalesce","is_null":"is_null"}
BINARY={ast.Add:"add",ast.Sub:"sub",ast.Mult:"mul",ast.Div:"div"}
COMPARE={ast.Eq:"eq",ast.NotEq:"ne",ast.Gt:"gt",ast.GtE:"gte",ast.Lt:"lt",ast.LtE:"lte"}

class PythonFrontend:
    def __init__(self, env):
        self.env=env

    def fail(self,node,message):
        raise CompileError("UNSUPPORTED_SYNTAX",message,line=getattr(node,"lineno",None),
                           column=getattr(node,"col_offset",0)+1)

    def compile(self,source):
        if len(source)>32000: raise CompileError("COMPLEXITY_LIMIT","Source too long")
        try: tree=ast.parse(source)
        except SyntaxError as e:
            raise CompileError("SYNTAX_ERROR",e.msg,line=e.lineno,column=e.offset) from None
        stack=[(tree,0)];count=0
        while stack:
            current,depth=stack.pop();count+=1
            if count>1000 or depth>60: raise CompileError("COMPLEXITY_LIMIT","AST node/depth limit exceeded")
            stack.extend((child,depth+1) for child in ast.iter_child_nodes(current))
        if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):
            self.fail(tree,"Exactly one function; no imports or module-level statements")
        for candidate in ast.walk(tree):
            if isinstance(candidate,ast.stmt) and not isinstance(candidate,(ast.FunctionDef,ast.Assign,ast.If,ast.Return)):
                self.fail(candidate,"Statement is outside the language, even in an unreachable branch")
            if isinstance(candidate,ast.FunctionDef) and candidate is not tree.body[0]:
                self.fail(candidate,"Nested functions are not supported")
            if isinstance(candidate,ast.Call) and (not isinstance(candidate.func,ast.Name) or candidate.func.id not in CALLS):
                self.fail(candidate,"Only catalogued DSL calls are allowed")
        fn=tree.body[0]; a=fn.args
        if (fn.decorator_list or a.defaults or a.kw_defaults or a.kwonlyargs or a.vararg or a.kwarg
            or a.posonlyargs or [v.arg for v in a.args] not in (["inputs"],["inputs","variables"],["inputs","variables","constants"])
            or any(v.annotation is not None for v in a.args)
            or not isinstance(fn.returns,ast.Name) or fn.returns.id!="bool"):
            self.fail(fn,"Use def name(inputs, variables, constants) -> bool without decorators/defaults")
        self.parameters={v.arg for v in a.args}
        self.fn=fn
        result=self.block(fn.body,{})
        from .validation import bounded
        bounded(result)
        try:
            if infer(result,self.env)!=BOOL:
                raise CompileError("NON_BOOLEAN_RETURN","Every return path must be non-null Boolean")
        except CompileError as e:
            if e.diagnostic.line is None:
                e.diagnostic.line=fn.lineno;e.diagnostic.column=fn.col_offset+1
            raise
        return result

    def block(self,statements,locals_):
        if not statements:
            raise CompileError("NON_BOOLEAN_RETURN","A path implicitly returns None",line=self.fn.lineno)
        first,*rest=statements
        if isinstance(first,ast.Return):
            if rest: self.fail(rest[0],"Unreachable statements are not supported")
            if first.value is None or (isinstance(first.value,ast.Constant) and first.value.value is None):
                raise CompileError("NON_BOOLEAN_RETURN","return None is not a rule result",line=first.lineno)
            return self.expression(first.value,locals_)
        if isinstance(first,ast.Assign) and len(first.targets)==1 and isinstance(first.targets[0],ast.Name):
            name=first.targets[0].id
            if name in locals_ or name in SCOPES or name in CALLS:
                self.fail(first,"Only single-assignment local names")
            value=self.expression(first.value,locals_)
            return op("let",value,self.block(rest,{**locals_,name:ref("local",name)}),name=name)
        if isinstance(first,ast.If):
            condition=self.expression(first.test,locals_)
            def branch(body):
                # A direct return completes this branch; otherwise append the continuation.
                return self.block(body if body and isinstance(body[-1],ast.Return) else body+rest,dict(locals_))
            return op("if",condition,branch(first.body),branch(first.orelse))
        self.fail(first,"Only assignments, if/else and return are supported")

    def expression(self,node,locals_,in_predicate=False):
        try: return self._expression(node,locals_,in_predicate)
        except CompileError as e:
            if e.diagnostic.line is None:
                e.diagnostic.line=getattr(node,"lineno",None)
                e.diagnostic.column=getattr(node,"col_offset",0)+1
            raise

    def _expression(self,node,locals_,in_predicate=False):
        recur=lambda n:self.expression(n,locals_,in_predicate)
        if isinstance(node,ast.Constant): return literal(node.value)
        if isinstance(node,ast.Name) and node.id in locals_: return deepcopy(locals_[node.id])
        if isinstance(node,ast.Subscript):
            path=[];current=node
            while isinstance(current,ast.Subscript):
                if not isinstance(current.slice,ast.Constant) or not isinstance(current.slice.value,str):
                    self.fail(node,"Field paths require literal string keys")
                path.insert(0,current.slice.value);current=current.value
            if not isinstance(current,ast.Name) or current.id not in SCOPES:
                self.fail(node,"Reference inputs, variables, constants or predicate item")
            if current.id=="item" and not in_predicate: self.fail(node,"item outside predicate")
            if current.id!="item" and current.id not in self.parameters: self.fail(node,"Undeclared parameter")
            return ref(SCOPES[current.id],*path)
        if isinstance(node,ast.BinOp) and type(node.op) in BINARY:
            return op(BINARY[type(node.op)],recur(node.left),recur(node.right))
        if isinstance(node,ast.BoolOp):
            return op("and" if isinstance(node.op,ast.And) else "or",*(recur(v) for v in node.values))
        if isinstance(node,ast.UnaryOp):
            if isinstance(node.op,ast.Not): return op("not",recur(node.operand))
            if isinstance(node.op,ast.USub):
                if isinstance(node.operand,ast.Constant):
                    if type(node.operand.value) not in (int,float): self.fail(node,"Unary minus requires a number")
                    return literal(-node.operand.value)
                return op("sub",literal(0),recur(node.operand))
        if isinstance(node,ast.IfExp): return op("if",recur(node.test),recur(node.body),recur(node.orelse))
        if isinstance(node,ast.Compare):
            comparisons=[];left=node.left
            for operation,right in zip(node.ops,node.comparators):
                if isinstance(operation,(ast.Is,ast.IsNot)) and isinstance(right,ast.Constant) and right.value is None:
                    part=op("is_null",recur(left))
                    if isinstance(operation,ast.IsNot): part=op("not",part)
                elif type(operation) in COMPARE:
                    part=op(COMPARE[type(operation)],recur(left),recur(right))
                else: self.fail(node,"Unsupported comparison")
                comparisons.append(part);left=right
            return comparisons[0] if len(comparisons)==1 else op("and",*comparisons)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords and node.func.id in CALLS:
            name=CALLS[node.func.id]
            if name in ("exists","all"):
                if len(node.args)!=2 or not isinstance(node.args[1],ast.Lambda): self.fail(node,"Array predicates require lambda item")
                lam=node.args[1]
                if (len(lam.args.args)!=1 or lam.args.args[0].arg!="item" or lam.args.defaults
                    or lam.args.kwonlyargs or lam.args.vararg or lam.args.kwarg or lam.args.posonlyargs):
                    self.fail(lam,"Predicate signature is lambda item")
                return op(name,recur(node.args[0]),self.expression(lam.body,locals_,True))
            if name in ("sum","min","max","mean") and len(node.args)==2:
                if not isinstance(node.args[1],ast.Constant) or not isinstance(node.args[1].value,str):
                    self.fail(node,"Aggregate path must be a literal string")
                return op(name,recur(node.args[0]),path=node.args[1].value.split("."))
            return op(name,*(recur(v) for v in node.args))
        self.fail(node,f"Unsupported construct: {type(node).__name__}")

def compile_python(source, env):
    return PythonFrontend(env).compile(source)

SQL_BINARY={exp.Add:"add",exp.Sub:"sub",exp.Mul:"mul",exp.Div:"div",
            exp.EQ:"eq",exp.NEQ:"ne",exp.GT:"gt",exp.GTE:"gte",exp.LT:"lt",exp.LTE:"lte",
            exp.And:"and",exp.Or:"or"}
SQL_CALLS={"DSL_SUM":"sum","DSL_COUNT":"count","DSL_MIN":"min","DSL_MAX":"max","DSL_MEAN":"mean",
           "DSL_EXISTS":"exists","DSL_ALL":"all"}

def compile_sql(source, env):
    if len(source)>32000: raise CompileError("COMPLEXITY_LIMIT","Source too long")
    try: trees=sqlglot.parse(source,read="duckdb")
    except sqlglot.errors.ParseError as e: raise CompileError("SYNTAX_ERROR",str(e)) from None
    if len(trees)!=1 or trees[0] is None: raise CompileError("UNSUPPORTED_SYNTAX","One SQL expression only")
    node=trees[0]
    stack=[(node,0)];count=0
    while stack:
        current,depth=stack.pop();count+=1
        if count>1000 or depth>60: raise CompileError("COMPLEXITY_LIMIT","SQL node/depth limit exceeded")
        stack.extend((child,depth+1) for child in current.iter_expressions())
    if isinstance(node,exp.Select):
        if len(node.expressions)!=1 or any(v for k,v in node.args.items() if k!="expressions"):
            raise CompileError("UNSUPPORTED_SYNTAX","SELECT one expression, without FROM or other clauses")
        node=node.expressions[0]
    def convert(n):
        if isinstance(n,exp.Paren): return convert(n.this)
        if type(n) in SQL_BINARY: return op(SQL_BINARY[type(n)],convert(n.this),convert(n.expression))
        if isinstance(n,exp.Not): return op("not",convert(n.this))
        if isinstance(n,exp.Neg):
            if isinstance(n.this,exp.Literal) and not n.this.is_string:
                return literal(-Decimal(n.this.this) if "." in n.this.this else -int(n.this.this))
            return op("sub",literal(0),convert(n.this))
        if isinstance(n,exp.Boolean): return literal(n.this)
        if isinstance(n,exp.Literal):
            return literal(n.this if n.is_string else Decimal(n.this) if "." in n.this or "e" in n.this.lower() else int(n.this))
        if isinstance(n,exp.Column):
            parts=[p.name for p in n.parts]
            if len(parts)<2 or parts[0] not in SCOPES:
                raise CompileError("UNKNOWN_FIELD","Qualify fields as inputs.x, variables.x, constants.x or item.x")
            return ref(SCOPES[parts[0]],*parts[1:])
        if isinstance(n,exp.Is) and isinstance(n.expression,exp.Null): return op("is_null",convert(n.this))
        if isinstance(n,exp.Coalesce):
            args=[n.this,*n.expressions]
            if len(args)!=2: raise CompileError("ARITY","COALESCE requires two arguments")
            return op("coalesce",*(convert(a) for a in args))
        if isinstance(n,exp.Case):
            if n.this is not None or n.args.get("default") is None:
                raise CompileError("UNSUPPORTED_SYNTAX","Use searched CASE with ELSE")
            result=convert(n.args["default"])
            for case in reversed(n.args["ifs"]):
                result=op("if",convert(case.this),convert(case.args["true"]),result)
            return result
        if isinstance(n,exp.Anonymous) and n.name.upper() in SQL_CALLS:
            name=SQL_CALLS[n.name.upper()];args=n.expressions
            if name in ("sum","min","max","mean") and len(args)==2:
                if not isinstance(args[1],exp.Literal) or not args[1].is_string:
                    raise CompileError("UNSUPPORTED_SYNTAX","Aggregate field path must be a string")
                return op(name,convert(args[0]),path=args[1].this.split("."))
            return op(name,*(convert(a) for a in args))
        raise CompileError("UNSUPPORTED_SYNTAX",f"SQL construct not supported: {type(n).__name__}")
    result=convert(node)
    if infer(result,env)!=BOOL: raise CompileError("NON_BOOLEAN_RETURN","SQL rule must return non-null Boolean")
    return result
