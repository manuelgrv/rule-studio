"""Build browser assets from the existing synthetic generator and portable engine."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import shutil
import duckdb
from rule_manager.synthetic import generate_banking_data, ALLOWED_TABLES
from rule_manager.examples import input_definition, evaluation_definition

root = Path(__file__).resolve().parents[1]
out = root / 'web/public/demo'
out.mkdir(parents=True, exist_ok=True)
# Always generate an isolated synthetic dataset; never export an arbitrary bank DB.
db = duckdb.connect(':memory:')
generate_banking_data(db, clients=30000, seed=20260909)
for table in ALLOWED_TABLES:
    target = str(out / f'{table}.parquet').replace("'", "''")
    db.execute(f"COPY {table} TO '{target}' (FORMAT PARQUET)")
inputs = input_definition()
(out / 'defaults.json').write_text(json.dumps({'inputs': inputs, 'evaluations': evaluation_definition(inputs)}, indent=2))
with ZipFile(out / 'rule_manager.zip', 'w', ZIP_DEFLATED) as archive:
    for file in (root / 'src/rule_manager').rglob('*'):
        if file.suffix in ('.py', '.json'):
            archive.write(file, file.relative_to(root / 'src'))
shutil.copy(root / 'web/python/bridge.py', out / 'bridge.py')
print('Prepared 30,000 synthetic clients, source tables, DSL examples and portable compiler.')
