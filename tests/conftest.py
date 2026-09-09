import duckdb
import pytest
from rule_manager.synthetic import generate_banking_data,ALLOWED_TABLES
from rule_manager.duckdb_backend import DuckDBBackend
from rule_manager.examples import input_definition,evaluation_definition
from rule_manager.validation import validate_evaluations

@pytest.fixture
def db():
    con=duckdb.connect(":memory:")
    generate_banking_data(con,20)
    yield con
    con.close()

@pytest.fixture
def backend(db): return DuckDBBackend(db,ALLOWED_TABLES)

@pytest.fixture
def definitions():
    inputs=input_definition()
    return inputs,evaluation_definition(inputs)

@pytest.fixture
def env(definitions):
    i,e=definitions
    return validate_evaluations(e,i)[1]
