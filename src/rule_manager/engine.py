from copy import deepcopy
from .errors import EvaluationError, CompileError
from .types import value_as, BOOL
from .expressions import evaluate_expression, decode_literal, dependencies
from .validation import validate_evaluations

class EvaluationPlan:
    """Validated portable plan; the local interpreter is not a distributed runtime."""
    def __init__(self,document,input_definition):
        self.document=deepcopy(document)
        document=self.document
        self.input_definition=deepcopy(input_definition)
        self.variables,self.env=validate_evaluations(document,input_definition)
        self.rules={r["id"]:r for r in document["rules"]}
        self.products={p["id"]:p for p in document["products"]}

    def evaluate_client(self, fields, selected_products=None):
        value_as(fields,self.input_definition["output_schema"])
        selected=list(self.products) if selected_products is None else list(selected_products)
        if not selected or len(set(selected))!=len(selected) or any(p not in self.products for p in selected):
            raise CompileError("UNKNOWN_PRODUCT","Select existing distinct products")
        needed_rules=set().union(*(dependencies(self.products[p]["expression"],"rule") for p in selected))
        needed_variables=set()
        for name in needed_rules: needed_variables |= dependencies(self.rules[name]["expression"],"variable")
        for var in reversed(self.variables):
            if var["id"] in needed_variables:
                needed_variables |= dependencies(var["expression"],"variable")
        context={"input":fields,"constant":{k:decode_literal(v) for k,v in self.document["constants"].items()},
                 "variable":{},"rule":{}}
        def run(entry,typ):
            try:
                value=value_as(evaluate_expression(entry["expression"],context),typ)
                return {"value":value,"error":None}
            except EvaluationError as e:
                return {"value":None,"error":{"code":e.code,"message":str(e)}}
        variable_results=[]
        for var in self.variables:
            if var["id"] not in needed_variables: continue
            result=run(var,var["data_type"]);context["variable"][var["id"]]=result
            variable_results.append({"id":var["id"],"version":var["version"],"data_type":var["data_type"],
                                     "dependencies":sorted(dependencies(var["expression"],"variable")),
                                     **result})
        rule_results=[]
        for name,entry in self.rules.items():
            if name not in needed_rules: continue
            result=run(entry,BOOL);context["rule"][name]=result
            rule_results.append({"id":name,"version":entry["version"],**result})
        products=[]
        for name in selected:
            p=self.products[name]
            # No short circuit can hide an error in any referenced rule.
            refs=sorted(dependencies(p["expression"],"rule"))
            failed=[r for r in refs if context["rule"][r]["error"]]
            result=({"value":None,"error":{"code":"RULE_ERROR","message":", ".join(failed)}}
                    if failed else run(p,BOOL))
            products.append({"id":name,"version":p["version"],"rules":refs,**result})
        return {"variables":variable_results,"rules":rule_results,"products":products}
