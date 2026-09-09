"""Definitions also usable by a future visual editor; no separate visual compiler."""
from copy import deepcopy
from .types import BOOL,INT,DECIMAL,nullable
from .expressions import ref,literal,op,TypeEnvironment
from .validation import canonical_hash,validate_evaluations
from .authoring import compile_python,compile_sql

STRING={"type":"string","nullable":False}
MONEY={"type":"decimal","precision":18,"scale":2,"nullable":False}
DATE={"type":"date","nullable":False}

def struct(fields,nullable=False): return {"type":"struct","nullable":nullable,"fields":fields}
def array(fields): return {"type":"array","nullable":False,"items":struct(fields)}
def field(source,name): return {"ref":{"source":source,"field":name}}
def header(kind,name):
    return {"kind":kind,"dsl_version":"0.1","definition_id":name,"definition_version":1,
            "created_by":"synthetic-author","created_at":"2026-09-09T00:00:00Z"}

def input_definition():
    client_fields={"client_id":STRING,"name":STRING,"age":INT,"spouse_id":nullable(STRING)}
    financial_fields={"client_id":STRING,"income":MONEY,"debt":MONEY}
    account_fields={"account_id":STRING,"client_id":STRING,"balance":MONEY,"kind":STRING}
    movement_fields={"movement_id":STRING,"account_id":STRING,"amount":MONEY,"movement_date":DATE}
    loan_fields={"loan_id":STRING,"client_id":STRING,"outstanding":MONEY}
    source_specs=[("c","clients",client_fields),("f","finances",financial_fields),("sp","clients",client_fields),
                  ("sf","finances",financial_fields),("a","accounts",account_fields),("m","movements",movement_fields),
                  ("l","loans",loan_fields)]
    def join(id,parent,source,left,right,cardinality,order):
        return {"id":id,"parent":parent,"source":source,"left_key":left,"right_key":right,"cardinality":cardinality,"order_by":[order]}
    schema=struct({
        "name":STRING,"age":INT,"financial":struct({"income":MONEY,"debt":MONEY},True),
        "spouse":struct({"name":STRING,"financial":struct({"income":MONEY},True)},True),
        "accounts":array({"id":STRING,"balance":MONEY,"kind":STRING,
                          "movements":array({"id":STRING,"amount":MONEY,"date":DATE})}),
        "loans":array({"id":STRING,"outstanding":MONEY})})
    mappings={
        "name":field("c","name"),"age":field("c","age"),
        "financial":{"join":"financial","object":{"income":field("f","income"),"debt":field("f","debt")}},
        "spouse":{"join":"spouse","object":{"name":field("sp","name"),
                   "financial":{"join":"spouse_financial","object":{"income":field("sf","income")}}}},
        "accounts":{"join":"accounts","array":{"id":field("a","account_id"),"balance":field("a","balance"),"kind":field("a","kind"),
                    "movements":{"join":"movements","array":{"id":field("m","movement_id"),"amount":field("m","amount"),"date":field("m","movement_date")}}}},
        "loans":{"join":"loans","array":{"id":field("l","loan_id"),"outstanding":field("l","outstanding")}}}
    return deepcopy({**header("consolidated_inputs","banking_inputs"),
        "root":{"source":"c","client_key":"client_id"},
        "sources":[{"id":i,"table_ref":t,"fields":fields} for i,t,fields in source_specs],
        "joins":[join("financial","c","f","client_id","client_id","one","client_id"),
                 join("spouse","c","sp","spouse_id","client_id","one","client_id"),
                 join("spouse_financial","sp","sf","client_id","client_id","one","client_id"),
                 join("accounts","c","a","client_id","client_id","many","account_id"),
                 join("movements","a","m","account_id","account_id","many","movement_id"),
                 join("loans","c","l","client_id","client_id","many","loan_id")],
        "output_schema":schema,"mappings":mappings})

PYTHON_RULE='''def regla(inputs, variables, constants) -> bool:
    return inputs["age"] >= constants["minimum_age"]
'''
SQL_RULE="inputs.age >= constants.minimum_age"

def evaluation_definition(inputs):
    def entry(id,typ,expression): return {"id":id,"version":1,"data_type":typ,"expression":expression}
    variables=[
        entry("income",MONEY,op("coalesce",ref("input","financial","income"),ref("constant","zero_money"))),
        entry("debt",MONEY,op("coalesce",ref("input","financial","debt"),ref("constant","zero_money"))),
        entry("debt_ratio",DECIMAL,op("div",ref("variable","debt"),ref("variable","income"))),
        entry("total_balance",DECIMAL,op("sum",ref("input","accounts"),path=["balance"])),
        entry("account_count",INT,op("count",ref("input","accounts")))]
    doc={**header("evaluations","banking_evaluation"),
        "input_contract":{"definition_id":inputs["definition_id"],"definition_version":inputs["definition_version"],
                          "schema_hash":canonical_hash(inputs["output_schema"])},
        "constants":{"minimum_age":{"value":18,"data_type":INT},"zero_money":{"value":"0.00","data_type":MONEY}},
        "variables":variables,
        "rules":[entry("adult",BOOL,op("gte",ref("input","age"),ref("constant","minimum_age"))),
                 entry("affordability",BOOL,op("lt",ref("variable","debt_ratio"),literal(DecimalText("1.0")))),
                 entry("has_accounts",BOOL,op("gt",ref("variable","account_count"),literal(0))),
                 entry("non_negative_balance",BOOL,op("gte",ref("variable","total_balance"),literal(0)))],
        "products":[
            {"id":"basic_account","version":1,"expression":ref("rule","adult")},
            {"id":"demo_credit","version":1,"expression":op("and",ref("rule","adult"),ref("rule","affordability"))},
            {"id":"savings_offer","version":1,"expression":op("and",ref("rule","adult"),ref("rule","has_accounts"),ref("rule","non_negative_balance"))}]}
    _,env=validate_evaluations(doc,inputs)
    assert compile_python(PYTHON_RULE,env)==doc["rules"][0]["expression"]
    assert compile_sql(SQL_RULE,env)==doc["rules"][0]["expression"]
    return deepcopy(doc)

def DecimalText(value):
    from decimal import Decimal
    return Decimal(value)
