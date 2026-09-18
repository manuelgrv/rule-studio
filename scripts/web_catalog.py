"""Extended, deterministic synthetic catalog for the browser demo only."""
from copy import deepcopy
from rule_manager.examples import STRING, MONEY, DATE, struct, array, field
from rule_manager.types import INT, BOOL


def extend_catalog(db, inputs):
    additions = {
        'clients': {'email': (STRING, "lower(client_id) || '@example.test'"),
                    'city': (STRING, "CASE WHEN age % 2 = 0 THEN 'Lima' ELSE 'Arequipa' END"),
                    'country': (STRING, "'Perú'"), 'segment': (STRING, "CASE WHEN age < 30 THEN 'Inicial' ELSE 'Regular' END"),
                    'registered_date': (DATE, "DATE '2020-01-01' + CAST(age * 7 AS INTEGER)"),
                    'active': (BOOL, 'age % 9 != 0')},
        'finances': {'monthly_expenses': (MONEY, 'income * 0.35'), 'assets': (MONEY, 'income * 24'),
                     'savings': (MONEY, 'income * 3'), 'currency': (STRING, "'PEN'")},
        'accounts': {'currency': (STRING, "'PEN'"), 'status': (STRING, "'Activo'"),
                     'opened_date': (DATE, "DATE '2022-01-01'"), 'overdraft_limit': (MONEY, 'balance * 0.1')},
        'movements': {'channel': (STRING, "CASE WHEN amount > 500 THEN 'Web' ELSE 'Móvil' END"),
                      'category': (STRING, "CASE WHEN amount > 1000 THEN 'Servicios' ELSE 'Compras' END"),
                      'direction': (STRING, "'Salida'"), 'currency': (STRING, "'PEN'")},
        'loans': {'status': (STRING, "'Vigente'"), 'installment': (MONEY, 'outstanding / 12'),
                  'remaining_months': (INT, '12'), 'days_overdue': (INT, 'CAST(outstanding AS BIGINT) % 31')},
    }
    sql_types = {'string': 'VARCHAR', 'decimal': 'DECIMAL(18,2)', 'integer': 'BIGINT', 'date': 'DATE', 'boolean': 'BOOLEAN'}
    for table, fields in additions.items():
        for name, (typ, expression) in fields.items():
            db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {sql_types[typ["type"]]}')
            db.execute(f'UPDATE {table} SET {name} = {expression}')
        for source in inputs['sources']:
            if source['table_ref'] == table:
                source['fields'].update({name: deepcopy(typ) for name, (typ, _) in fields.items()})
    db.execute("""CREATE TABLE employment AS SELECT client_id, 'Empresa sintética ' || CAST(age % 20 AS VARCHAR) company,
      CASE WHEN age % 2 = 0 THEN 'Servicios' ELSE 'Tecnología' END sector,
      CASE WHEN age % 3 = 0 THEN 'Independiente' ELSE 'Dependiente' END contract_type,
      age % 15 tenure_years, CAST(age * 125 AS DECIMAL(18,2)) monthly_salary, true active FROM clients""")
    db.execute("""CREATE TABLE addresses AS SELECT client_id || '_' || CAST(n AS VARCHAR) address_id, client_id,
      CASE WHEN n = 1 THEN 'Residencia' ELSE 'Trabajo' END kind, city, country,
      '15001' postal_code, n = 1 is_primary FROM clients CROSS JOIN range(1,3) t(n)""")
    db.execute("""CREATE TABLE interactions AS SELECT client_id || '_' || CAST(n AS VARCHAR) interaction_id, client_id,
      DATE '2026-09-01' + CAST(n AS INTEGER) contact_date,
      CASE WHEN n = 1 THEN 'Web' ELSE 'Teléfono' END channel,
      'Consulta' category, 'Resuelto' outcome, (age + n) % 5 + 1 satisfaction
      FROM clients CROSS JOIN range(1,3) t(n)""")
    extras = [
      ('e', 'employment', {'client_id': STRING, 'company': STRING, 'sector': STRING, 'contract_type': STRING, 'tenure_years': INT, 'monthly_salary': MONEY, 'active': BOOL}, 'one', 'client_id'),
      ('ad', 'addresses', {'address_id': STRING, 'client_id': STRING, 'kind': STRING, 'city': STRING, 'country': STRING, 'postal_code': STRING, 'is_primary': BOOL}, 'many', 'address_id'),
      ('it', 'interactions', {'interaction_id': STRING, 'client_id': STRING, 'contact_date': DATE, 'channel': STRING, 'category': STRING, 'outcome': STRING, 'satisfaction': INT}, 'many', 'interaction_id'),
    ]
    for alias, table, fields, cardinality, order in extras:
        inputs['sources'].append({'id': alias, 'table_ref': table, 'fields': deepcopy(fields)})
        inputs['joins'].append({'id': table, 'parent': 'c', 'source': alias, 'left_key': 'client_id', 'right_key': 'client_id', 'cardinality': cardinality, 'order_by': [order]})
    # A complete optional selection template, separate from the initial saved DSL.
    catalog = deepcopy(inputs)
    branches = {'c': (), 'f': ('financial',), 'sp': ('spouse',), 'sf': ('spouse', 'financial'),
                'a': ('accounts',), 'm': ('accounts', 'movements'), 'l': ('loans',)}
    for alias, table, fields, cardinality, order in extras:
        branches[alias] = (table,)
        catalog['output_schema']['fields'][table] = array({}) if cardinality == 'many' else struct({}, True)
        catalog['mappings'][table] = {'join': table, 'array' if cardinality == 'many' else 'object': {}}
    for source in catalog['sources']:
        schema, mapping = catalog['output_schema'], catalog['mappings']
        for part in branches[source['id']]:
            schema = schema['fields'][part]
            if schema['type'] == 'array': schema = schema['items']
            mapping = mapping[part].get('object', mapping[part].get('array'))
        existing = {m['ref']['field'] for m in mapping.values() if 'ref' in m}
        for name, typ in source['fields'].items():
            if name not in existing:
                schema['fields'][name] = deepcopy(typ)
                mapping[name] = field(source['id'], name)
    return catalog
