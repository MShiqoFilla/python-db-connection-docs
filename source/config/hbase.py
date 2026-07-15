from dotenv import load_dotenv
import happybase
import os

load_dotenv()

class HBaseService:
    def __init__(self, **hbase_configs):
        self.hbase_host = hbase_configs["hbase_host"]
        self.hbase_port = hbase_configs["hbase_port"]

    def connect(self):
        connection =  happybase.Connection(host = self.hbase_host, port=self.hbase_port, autoconnect=True)
        connection.open()
        return connection
    
    def get_tables(self):
        client = self.connect()
        tables =  [table.decode() for table in client.tables()]
        client.close()
        return tables
    
    def create_table(self, table_name, families: dict):
        client = self.connect()
        client.create_table(name=table_name, families=families)
        client.close()
        return True

    def get_row(self, table: str, row: str, columns: list[str] = None):
        if columns and not isinstance(columns, list):
            raise ValueError("Columns passed should be in form of list")
        client = self.connect()
        active_table = self.client.table(table)
        client.close()
        return {key.decode() : value.decode() for key, value in active_table.row(row, columns).items()}

    def get_cell(self, table: str, row_key: str, column: str, all_versions : bool = False):
        client = self.connect()
        active_table = client.table(table)
        if all_versions:
            results = active_table.cells(row=row_key, column=column)
        else:
            results = active_table.cells(row=row_key, column=column, versions=1)
        client.close()
        return [res.decode() for res in results]

    def put_value_to_table(self, table: str, row_key: str, data: str, timestamp: int=None):
        client = self.connect()
        active_table = client.table(table)
        active_table.put(row=row_key, data=data, timestamp=timestamp)
        client.close()

    def scan_by_prefix(self, table: str, prefix, columns):
        client = self.connect()
        active_table = client.table(table)
        results = active_table.scan(row_prefix=prefix.encode(), columns=columns)
        client.close()
        return list(results)
    
def get_default_hbase_client():
    return HBaseService(hbase_host=os.getenv("HBASE_HOST"), hbase_port=os.getenv("HBASE_PORT"))