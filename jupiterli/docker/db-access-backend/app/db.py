import sqlite3, re

from .config import settings

def ch_to_sqlite_sql(sql):
    return re.sub(
        r'%\(([^)]+)\)s',
        r':\1',
        sql,
    )

class SQLiteQueryResult:
    def __init__(self, rows, column_names):
        self.result_rows = rows
        self.column_names = tuple(column_names)
        self.row_count = len(rows)
        
        self.result_columns = [
            [row[i] for row in rows]
            for i in range(len(column_names))
        ] if rows else [[] for _ in column_names]

class SQLiteClient:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def query(self, sql, parameters=None):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            new_sql = ch_to_sqlite_sql(sql)
            cur.execute(new_sql, parameters or ())
        
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return SQLiteQueryResult(rows, cols)

    def insert_rec(self, table_name, rec):
        with sqlite3.connect(self.db_path) as conn:
            columns = ", ".join(rec.keys())
            placeholders = ", ".join(f":{k}" for k in rec.keys())
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            #print("admin sql:", sql, row)
            conn.execute(sql, rec)
            conn.commit()

