import sys
import time
import redis, json
import sqlite3
from datetime import datetime

STREAM = "telemetry"
ADMIN_STREAM = "telemetry-admin"
GROUP = "ch_group"
CONSUMER = "consumer_1"

BATCH_SIZE = 1000
BLOCK_MS = 1000
FLUSH_INTERVAL_SEC = 2.0

def get_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + ":"

def create_all_tables(ch):
    qs = []
    qs.append("""
    CREATE TABLE IF NOT EXISTS runs_dets (
    run_id varchar,
    created_ts real, host varchar, pid integer,
    argv0 varcharg, args varchar, run_label varchar
    )
    """)
    
    qs.append("""
    create table if not exists series_dets (
    series_id varchar,
    run_id varchar,
    key varchar
    )
    """)

    qs.append("""
    create table if not exists series (
    series_id varchar,
    run_serial_num integer,
    timestamp real,
    value real
    )
    """)

    qs.append("""
    CREATE INDEX IF NOT EXISTS idx_series_sid_serial
    ON series(series_id, run_serial_num)
    """)

    print(get_ts(), "start of intake server")
    for q in qs:
        print(q)
        ch.execute(q)

class StreamToSqlite3:
    def __init__(self, sqlite3_db_fn):
        self.r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.ch = sqlite3.connect(sqlite3_db_fn)
        self.ch.execute("PRAGMA journal_mode=WAL")
        self.ch.execute("PRAGMA synchronous=NORMAL")
        self.ch.commit()        
        create_all_tables(self.ch)
        if 1: # verify WAL settings
            mode = self.ch.execute("PRAGMA journal_mode").fetchone()[0]
            sync = self.ch.execute("PRAGMA synchronous").fetchone()[0]
            print("journal_mode =", mode)
            print("synchronous =", sync)
            
        self.buffer = []

    def ensure_group(self):
        for stream in [STREAM, ADMIN_STREAM]:
            try:
                self.r.xgroup_create(name = stream, groupname = GROUP, id="$", mkstream=True)
            except redis.exceptions.ResponseError:
                #print("xgroup_create exception")
                pass  # group already exists

    def flush(self):
        if len(self.buffer) == 0:
            return

        print(get_ts(), f"flush: {len(self.buffer)} msgs")

        rows = []
        msg_ids = []

        for msg_id, data in self.buffer:
            try:
                data = json.loads(data.get('data'))
                rows.append(list(data.values()))
                msg_ids.append(msg_id)
            except Exception as e:
                print("exception", e)
                msg_ids.append(msg_id)

        self.buffer.clear()

        # 1. Insert into sqlite3
        cols = ",".join(list(data.keys()))
        placeholders = ",".join("?" * len(data))
        #print("inserting ", placeholders, rows, msg_ids)
        self.ch.executemany(f"insert into series({cols}) values ({placeholders})", rows)
        self.ch.commit()

        # 2. ACK only after successful insert
        if len(msg_ids) > 0:
            self.r.xack(STREAM, GROUP, *msg_ids)

    def process_admin_messages(self, messages):
        processed_msg_ids = []
        for msg_id, data in messages:
            #print("admin message:", data)
            table_name = data["table"]
            row = json.loads(data["row"])
            columns = ", ".join(row.keys())
            placeholders = ", ".join(f":{k}" for k in row.keys())
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            #print("sql:", sql, row)
            self.ch.execute(sql, row)
            self.ch.commit()
            self.r.publish(data['reply-to'], "OK")
            processed_msg_ids.append(msg_id)
        self.r.xack(ADMIN_STREAM, GROUP, *processed_msg_ids)
        
    def run(self):
        self.ensure_group()

        while True:
            resp = self.r.xreadgroup(GROUP, CONSUMER, {STREAM: ">", ADMIN_STREAM: ">"}, count=500, block=BLOCK_MS)

            if resp:
                for stream_name, messages in resp:
                    if stream_name == STREAM:
                        print(get_ts(), "nof messages:", len(messages))
                        for msg_id, data in messages:
                            self.buffer.append((msg_id, data))
                    elif stream_name == ADMIN_STREAM:
                        #print("ADMIN_STREAM:", messages)
                        self.process_admin_messages(messages)
                    else:
                        print("unknown stream_name:", stream_name)

            self.flush()

if __name__ == "__main__":
    sqlite3_db_fn = sys.argv[1]
    print(get_ts(), "db file:", sqlite3_db_fn)
    worker = StreamToSqlite3(sqlite3_db_fn)
    worker.run()
