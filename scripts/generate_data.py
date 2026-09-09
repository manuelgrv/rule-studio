"""Generate only source tables, preserving any existing database."""
import argparse
from pathlib import Path
import duckdb
from rule_manager.synthetic import generate_banking_data
parser=argparse.ArgumentParser()
parser.add_argument("--database",default="data/banking.duckdb")
parser.add_argument("--clients",type=int,default=30000)
parser.add_argument("--seed",type=int,default=20260909)
args=parser.parse_args()
Path(args.database).parent.mkdir(parents=True,exist_ok=True)
with duckdb.connect(args.database) as con:
    print(generate_banking_data(con,args.clients,args.seed))
