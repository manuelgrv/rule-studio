"""Compile retrieval/consolidation DSL into parameter-free, catalog-bound SQL."""
from dataclasses import dataclass
from copy import deepcopy
from .errors import CompileError
from .types import quote, sql_type, compatible
from .validation import validate_inputs, unique

@dataclass(frozen=True)
class CatalogTable:
    table: str
    fields: dict

@dataclass(frozen=True)
class InputPlan:
    sql: str
    definition: dict

def table_name(name):
    return ".".join(quote(part) for part in name.split("."))

def compile_inputs(document, catalog):
    doc=validate_inputs(document)
    sources=unique(doc["sources"]); joins=unique(doc["joins"])
    root=doc["root"]["source"]
    if root not in sources: raise CompileError("UNKNOWN_SOURCE",root)
    for source in sources.values():
        if source["table_ref"] not in catalog:
            raise CompileError("UNAUTHORIZED_SOURCE",source["table_ref"])
        actual=catalog[source["table_ref"]]
        for name,typ in source["fields"].items():
            if name not in actual.fields:
                raise CompileError("UNKNOWN_FIELD",f'{source["id"]}.{name}')
            if not compatible(typ,actual.fields[name]):
                raise CompileError("CATALOG_DRIFT",f'{source["id"]}.{name}: declared schema differs from catalog')
    if doc["root"]["client_key"] not in sources[root]["fields"]:
        raise CompileError("UNKNOWN_FIELD","Root client key")
    keytype=sources[root]["fields"][doc["root"]["client_key"]]
    if keytype["nullable"] or keytype["type"] not in ("string","integer"):
        raise CompileError("TYPE_MISMATCH","Client key must be non-null string or integer")
    reached={root};remaining=dict(joins);used_sources={root}
    while remaining:
        progressed=False
        for name,j in list(remaining.items()):
            if j["parent"] not in reached: continue
            if j["source"] not in sources: raise CompileError("UNKNOWN_SOURCE",j["source"])
            if j["source"] in used_sources:
                raise CompileError("CYCLIC_DEPENDENCY","A source alias must have one parent")
            parent=sources[j["parent"]]["fields"];child=sources[j["source"]]["fields"]
            if j["left_key"] not in parent or j["right_key"] not in child:
                raise CompileError("UNKNOWN_FIELD","Join key is not declared")
            if not compatible(parent[j["left_key"]],child[j["right_key"]],ignore_null=True):
                raise CompileError("TYPE_MISMATCH","Join key types differ")
            if parent[j["left_key"]]["type"] not in ("string","integer"):
                raise CompileError("TYPE_MISMATCH","Join keys must be string/integer")
            if any(k not in child for k in j["order_by"]): raise CompileError("UNKNOWN_FIELD","Unknown ordering key")
            used_sources.add(j["source"]);reached.add(j["source"]);remaining.pop(name);progressed=True
        if not progressed: raise CompileError("CYCLIC_DEPENDENCY","Disconnected or cyclic join graph")
    if reached!=set(sources): raise CompileError("UNUSED_SOURCE","Each declared source must be connected")
    def render_fields(mappings,typ,context):
        if typ["type"]!="struct" or set(mappings)!=set(typ["fields"]):
            raise CompileError("OUTPUT_SCHEMA_MISMATCH","Mapping keys must equal struct field keys")
        return "struct_pack(" + ", ".join(f'{quote(k)} := {render(v,typ["fields"][k],context)}' for k,v in mappings.items()) + ")"
    def render(node,typ,context):
        if "ref" in node:
            if "join" in node:
                if node["join"] not in joins: raise CompileError("UNKNOWN_JOIN",node["join"])
                j=joins[node["join"]]
                if j["cardinality"]!="one" or j["parent"] not in context or j["source"] in context or node["ref"]["source"]!=j["source"]:
                    raise CompileError("INVALID_JOIN_PATH","Scalar join must be 1:1 from current context")
                body=render({"ref":node["ref"]},typ,context|{j["source"]})
                target=table_name(catalog[sources[j["source"]]["table_ref"]].table)
                predicate=f'{quote(j["source"])}.{quote(j["right_key"])} = {quote(j["parent"])}.{quote(j["left_key"])}'
                return f'(SELECT {body} FROM {target} AS {quote(j["source"])} WHERE {predicate})'
            r=node["ref"];src=r["source"]
            if src not in context or r["field"] not in sources[src]["fields"]:
                raise CompileError("UNKNOWN_FIELD","Reference outside current join context")
            source_type=sources[src]["fields"][r["field"]]
            if not compatible(source_type,typ,ignore_null=True) or (source_type["nullable"] and not typ["nullable"]):
                raise CompileError("TYPE_MISMATCH","Output field type/nulllability differs from source")
            return f'{quote(src)}.{quote(r["field"])}'
        collection="array" in node
        if collection and (typ["type"]!="array" or typ["nullable"] or typ["items"]["nullable"]):
            raise CompileError("TYPE_MISMATCH","A 1:N mapping is a non-null array of non-null objects")
        object_type=typ["items"] if collection else typ
        if "join" not in node:
            if collection: raise CompileError("MISSING_JOIN","Array requires a join")
            return render_fields(node["object"],object_type,context)
        if node["join"] not in joins: raise CompileError("UNKNOWN_JOIN",node["join"])
        j=joins[node["join"]]
        if j["parent"] not in context or j["source"] in context:
            raise CompileError("INVALID_JOIN_PATH","Join parent not in current context")
        if (j["cardinality"]=="many") != collection:
            raise CompileError("CARDINALITY_MISMATCH","Mapping and join cardinalities differ")
        alias=j["source"]
        body=render_fields(node["array" if collection else "object"],object_type,context|{alias})
        target=table_name(catalog[sources[alias]["table_ref"]].table)
        predicate=f'{quote(alias)}.{quote(j["right_key"])} = {quote(j["parent"])}.{quote(j["left_key"])}'
        if collection:
            ordering=", ".join(f'{quote(alias)}.{quote(k)}' for k in j["order_by"])
            body=f'coalesce(list({body} ORDER BY {ordering}), []::{sql_type(typ)})'
        return f'(SELECT {body} FROM {target} AS {quote(alias)} WHERE {predicate})'
    fields=render_fields(doc["mappings"],doc["output_schema"],{root})
    table=table_name(catalog[sources[root]["table_ref"]].table)
    sql=f'SELECT CAST({quote(root)}.{quote(doc["root"]["client_key"])} AS VARCHAR) AS client, CAST({fields} AS {sql_type(doc["output_schema"])}) AS fields FROM {table} AS {quote(root)}'
    return InputPlan(sql,deepcopy(doc))
