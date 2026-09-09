"""Browser transport adapter. All language semantics come from rule_manager."""
import json
from decimal import Decimal
from datetime import date, datetime
from copy import deepcopy
from rule_manager.inputs import compile_inputs, CatalogTable
from rule_manager.validation import validate_evaluations, canonical_hash
from rule_manager.api import compile_rule
from rule_manager.expressions import infer, dependencies
from rule_manager.engine import EvaluationPlan

def decode(value, typ):
    if value is None: return None
    if typ['type'] == 'struct': return {k:decode(value[k], t) for k,t in typ['fields'].items()}
    if typ['type'] == 'array': return [decode(v, typ['items']) for v in value]
    if typ['type'] == 'date': return date.fromisoformat(value)
    if typ['type'] == 'timestamp': return datetime.fromisoformat(value)
    return value

def dispatch(raw):
    req=json.loads(raw)
    inp=req['inputs']; doc=deepcopy(req.get('evaluations'))
    # Catalog is supplied from the fixed synthetic manifest, never the edited DSL.
    catalog={s['table_ref']:CatalogTable(s['table_ref'],s['fields']) for s in req['catalog']}
    plan=compile_inputs(inp,catalog)
    action=req['action']
    if action=='inputs': return {'sql':plan.sql,'hash':canonical_hash(inp['output_schema'])}
    if action=='rebind':
        doc['input_contract']={'definition_id':inp['definition_id'],'definition_version':inp['definition_version'],'schema_hash':canonical_hash(inp['output_schema'])}
    if action in ('rule','variable'):
        # An incomplete new rule is compiled against the existing valid package.
        _,env=validate_evaluations(doc,inp)
        if action=='rule': return compile_rule(req['source'],req['language'],env).to_dict()
        expr=req['expression']
        return {'id':req['id'],'version':1,'data_type':infer(expr,env),'expression':expr}
    ordered,env=validate_evaluations(doc,inp)
    if action=='evaluate':
        engine=EvaluationPlan(doc,inp)
        rows=json.loads(req['rows'],parse_float=Decimal)
        return [{'client':r['client'],**engine.evaluate_client(decode(r['fields'],inp['output_schema']))} for r in rows]
    return {'evaluations':doc,'sql':plan.sql,'variables':[{'id':v['id'],'dependencies':sorted(dependencies(v['expression'],'variable'))} for v in ordered]}

def call(raw):
    try: return json.dumps({'ok':True,'result':dispatch(raw)},default=str)
    except Exception as exc: return json.dumps({'ok':False,'error':{'code':getattr(exc,'code','COMPILATION_ERROR'),'message':str(exc)}})
