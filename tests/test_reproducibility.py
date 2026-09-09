import duckdb
from rule_manager.synthetic import generate_banking_data

def test_same_seed_identical_sources():
    a=duckdb.connect(":memory:");b=duckdb.connect(":memory:")
    try:
        generate_banking_data(a,10,7);generate_banking_data(b,10,7)
        for t in ("clients","finances","accounts","movements","loans"):
            assert a.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall()==b.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall()
    finally:
        a.close();b.close()
