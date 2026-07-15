from sqlalchemy import create_engine, URL, text, Engine
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

def _create_engine(
        user:str, password:str, dbname:str, host:str, port:int=5432
):
    return create_engine(
        url=URL.create(
            drivername="postgresql+psycopg2", username=user, 
            password=password, host=host, port=port, database=dbname
        ),
        pool_size=10,
        max_overflow=5,
        pool_timeout=5,
        pool_recycle=1800,
    )

class PostgreService:
    def __init__(self, engine : Engine):
        self.engine = engine

    def insert_on_conflict_do_update(self, table, conn, keys, data_iter):
        data = [dict(zip(keys, row)) for row in data_iter]
        insert_statement = insert(table.table).values(data)
        conflict_update = insert_statement.on_conflict_do_update(
            constraint=f"{table.table.name}_pkey",
            set_={column.key: column for column in insert_statement.excluded},
        )
        result = conn.execute(conflict_update)
        return result.rowcount
    
    def ingest(self, df: pd.DataFrame, schema: str, table_name: str):
        with self.engine.connect() as connect:
            df.to_sql(table_name, con=connect, if_exists='append', index=False, method=self.insert_on_conflict_do_update, schema=schema)
            connect.commit() 

    def ingest_replace(self, df: pd.DataFrame, schema: str, table_name: str):
        with self.engine.connect() as connect:
            df.to_sql(table_name, con=connect, if_exists="replace", index=False, schema=schema)
            connect.commit() 

    def execute_sql_select(self, query, params:dict|None=None):
        with self.engine.connect() as connect:
            return pd.read_sql(text(query), con=connect, params=params)
    
    def execute_sql_dml(self, query, params = None):
        with self.engine.connect() as connect:
            connect.execute(text(query), params or {})
            connect.commit()

def get_default_pg_engine():
    engine = _create_engine(
        user=os.getenv("PG_USER"), password=os.getenv("PG_PASS"),
        dbname=os.getenv("PG_DBNM"), host=os.getenv("PG_HOST"), port=os.getenv("PG_PORT")
    )
    return PostgreService(engine)