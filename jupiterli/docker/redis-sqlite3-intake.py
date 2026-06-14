import sys
import time
import redis, json
import sqlite3

STREAM = "telemetry"
ADMIN_STREAM = "telemetry-admin"
GROUP = "ch_group"
CONSUMER = "consumer_1"

BATCH_SIZE = 1000
BLOCK_MS = 1000
FLUSH_INTERVAL_SEC = 2.0
last_flush = time.time()

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

    for q in qs:
        print(q)
        ch.execute(q)

class StreamToSqlite3:
    def __init__(self, sqlite3_db_fn):
        self.r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.ch = sqlite3.connect(sqlite3_db_fn)
        create_all_tables(self.ch)
        self.buffer = []

    def ensure_group(self):
        for stream in [STREAM, ADMIN_STREAM]:
            try:
                self.r.xgroup_create(name = stream, groupname = GROUP, id="$", mkstream=True)
            except redis.exceptions.ResponseError:
                #print("xgroup_create exception")
                pass  # group already exists

    def flush(self):
        if not self.buffer:
            return

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
        global last_flush
        last_flush = time.time()

        # 1. Insert into sqlite3
        cols = ",".join(list(data.keys()))
        placeholders = ",".join("?" * len(data))
        #print("inserting ", rows)
        self.ch.executemany(f"insert into series({cols}) values ({placeholders})", rows)
        self.ch.commit()

        # 2. ACK only after successful insert
        if msg_ids:
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
            #print("sql:", sql)
            self.ch.execute(sql, row)
            self.ch.commit()
            self.r.publish(data['reply-to'], "OK")
            processed_msg_ids.append(msg_id)
        self.r.xack(ADMIN_STREAM, GROUP, *processed_msg_ids)
        
    def run(self):
        self.ensure_group()

        while True:
            resp = self.r.xreadgroup(GROUP, CONSUMER, {STREAM: ">", ADMIN_STREAM: ">"}, count=500, block=BLOCK_MS)

            if not resp:
                continue
            
            for stream_name, messages in resp:
                if stream_name == STREAM:
                    for msg_id, data in messages:
                        self.buffer.append((msg_id, data))
                elif stream_name == ADMIN_STREAM:
                    #print("ADMIN_STREAM:", messages)
                    self.process_admin_messages(messages)
                else:
                    print("unknown stream_name:", stream_name)

            # flush by size
            if len(self.buffer) >= BATCH_SIZE:
                self.flush()
            elif time.time() - last_flush > FLUSH_INTERVAL_SEC:
                self.flush()

            # optional periodic flush (low latency)
            else:
                time.sleep(0.01)


if __name__ == "__main__":
    sqlite3_db_fn = sys.argv[1]
    print("db file:", sqlite3_db_fn)
    worker = StreamToSqlite3(sqlite3_db_fn)
    worker.run()
