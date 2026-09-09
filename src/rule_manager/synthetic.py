"""Deterministic fictional banking fixture using Faker. Never reads bank data."""
import csv
import random
import tempfile
from decimal import Decimal
from pathlib import Path
from faker import Faker
from .errors import CompileError

ALLOWED_TABLES={"clients":"clients","finances":"finances","accounts":"accounts","movements":"movements","loans":"loans"}

def generate_banking_data(connection,clients=30000,seed=20260909):
    if clients<4: raise ValueError("At least four clients are needed for demonstration cases")
    if any(connection.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?",[t]).fetchone()[0] for t in ALLOWED_TABLES):
        raise CompileError("FIXTURE_EXISTS","Use a fresh database; generator never replaces existing source tables")
    fake=Faker("es_ES");fake.seed_instance(seed);rng=random.Random(seed)
    def money(): return Decimal(rng.randrange(10000,900000))/100
    client_rows=[];financial_rows=[];account_rows=[];movement_rows=[];loan_rows=[]
    for i in range(clients):
        cid=f"C{i:06d}"
        spouse=f"C{i+1:06d}" if i%4==0 and i+1<clients else None
        client_rows.append((cid,"SINTÉTICO "+fake.name(),40 if i<4 else rng.randint(18,85),spouse))
        financial_rows.append((cid,Decimal("0.00") if i%997==0 else money(),money()))
        count=0 if i==1 else 2 if i==2 else rng.randrange(4)
        for a in range(count):
            aid=f"A{i:06d}_{a}"
            account_rows.append((aid,cid,money(),rng.choice(["ahorro","corriente"])))
            for m in range(3 if i==2 else rng.randrange(4)):
                movement_rows.append((f"T{i:06d}_{a}_{m}",aid,money(),f"2026-09-{m+1:02d}"))
        for n in range(3 if i==2 else rng.randrange(3)):
            loan_rows.append((f"L{i:06d}_{n}",cid,money()))
    data={
      "clients":("client_id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, age BIGINT NOT NULL, spouse_id VARCHAR",
                 ["client_id","name","age","spouse_id"],client_rows),
      "finances":("client_id VARCHAR NOT NULL, income DECIMAL(18,2) NOT NULL, debt DECIMAL(18,2) NOT NULL",
                  ["client_id","income","debt"],financial_rows),
      "accounts":("account_id VARCHAR PRIMARY KEY, client_id VARCHAR NOT NULL, balance DECIMAL(18,2) NOT NULL, kind VARCHAR NOT NULL",
                  ["account_id","client_id","balance","kind"],account_rows),
      "movements":("movement_id VARCHAR PRIMARY KEY, account_id VARCHAR NOT NULL, amount DECIMAL(18,2) NOT NULL, movement_date DATE NOT NULL",
                   ["movement_id","account_id","amount","movement_date"],movement_rows),
      "loans":("loan_id VARCHAR PRIMARY KEY, client_id VARCHAR NOT NULL, outstanding DECIMAL(18,2) NOT NULL",
               ["loan_id","client_id","outstanding"],loan_rows)}
    connection.execute("BEGIN")
    try:
        with tempfile.TemporaryDirectory(prefix="rule-manager-fixture-") as tmp:
            for name,(ddl,columns,rows) in data.items():
                connection.execute(f"CREATE TABLE {name} ({ddl})")
                path=Path(tmp)/(name+".csv")
                with path.open("w",newline="") as f:
                    writer=csv.writer(f);writer.writerow(columns);writer.writerows(rows)
                escaped=str(path).replace("'","''")
                connection.execute(f"COPY {name} FROM '{escaped}' (HEADER, NULLSTR '')")
        connection.execute("CREATE TABLE synthetic_manifest(seed BIGINT,clients BIGINT,generator VARCHAR)")
        connection.execute("INSERT INTO synthetic_manifest VALUES (?,?,'Faker + random; fictional banking')",[seed,clients])
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK");raise
    return {name:len(rows) for name,(_,_,rows) in data.items()}
