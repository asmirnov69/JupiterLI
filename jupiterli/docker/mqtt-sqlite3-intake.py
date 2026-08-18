import sys
import time
import redis, json
import sqlite3
from datetime import datetime

STREAM = "telemetry"
ADMIN_STREAM = "telemetry-admin"

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

    # Replaces redis consumer-group bookkeeping: the last stream id we've
    # durably applied to sqlite, per stream. This is updated in the same
    # transaction as the data it protects, so a restart can resume without
    # a group's PEL (pending entries list).
    qs.append("""
    CREATE TABLE IF NOT EXISTS stream_checkpoints (
    stream_name varchar PRIMARY KEY,
    last_id varchar
    )
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
        # Next read position per stream, passed straight to XREAD. "$" means
        # "only entries added from now on" and is used until load_checkpoints()
        # finds a real resume point on disk.
        self.last_ids = {STREAM: "$", ADMIN_STREAM: "$"}

    def load_checkpoints(self):
        for stream in (STREAM, ADMIN_STREAM):
            row = self.ch.execute(
                "SELECT last_id FROM stream_checkpoints WHERE stream_name = ?",
                (stream,),
            ).fetchone()
            if row:
                self.last_ids[stream] = row[0]
        print(get_ts(), "resuming from", self.last_ids)

    def _save_checkpoint(self, stream_name, last_id):
        # Caller is responsible for the commit. Doing this insert in the same
        # transaction as the data it checkpoints is what makes resuming after
        # a restart safe - this is the replacement for xack.
        self.ch.execute(
            """
            INSERT INTO stream_checkpoints(stream_name, last_id) VALUES (?, ?)
            ON CONFLICT(stream_name) DO UPDATE SET last_id = excluded.last_id
            """,
            (stream_name, last_id),
        )
        self.last_ids[stream_name] = last_id

    def flush(self):
        if len(self.buffer) == 0:
            return

        print(get_ts(), f"flush: {len(self.buffer)} msgs")

        rows = []
        cols = None
        last_id = None

        for msg_id, data in self.buffer:
            last_id = msg_id  # buffer is in ascending redis-id order
            try:
                parsed = json.loads(data.get('data'))
                rows.append(list(parsed.values()))
                cols = list(parsed.keys())
            except Exception as e:
                print("exception parsing", msg_id, ":", e)

        self.buffer.clear()

        # 1. Insert into sqlite3
        if rows:
            try:
                cols_str = ",".join(cols)
                placeholders = ",".join("?" * len(cols))
                self.ch.executemany(f"insert into series({cols_str}) values ({placeholders})", rows)
            except Exception as e:
                # Drop the batch instead of crash-looping on it forever. With
                # no consumer group PEL, a crash here would just replay the
                # same bad batch again from the checkpoint after restart.
                print("exception inserting batch, dropping", len(rows), "rows:", e)
                self.ch.rollback()

        # 2. Checkpoint + commit together, so the read position only moves
        # past a batch once it has been durably applied (or deliberately
        # dropped, per above).
        if last_id is not None:
            self._save_checkpoint(STREAM, last_id)
            self.ch.commit()

    def process_admin_messages(self, messages):
        for msg_id, data in messages:
            reply_to = data.get("reply-to")
            ok = True
            try:
                table_name = data["table"]
                row = json.loads(data["row"])
                columns = ", ".join(row.keys())
                placeholders = ", ".join(f":{k}" for k in row.keys())
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                self.ch.execute(sql, row)
            except Exception as e:
                print("exception processing admin message", msg_id, ":", e)
                self.ch.rollback()
                ok = False

            # Advance the checkpoint either way so a single bad message can't
            # wedge the stream forever - same skip-and-move-on approach as
            # the malformed-JSON case in flush().
            self._save_checkpoint(ADMIN_STREAM, msg_id)
            self.ch.commit()

            if reply_to:
                self.r.publish(reply_to, "OK" if ok else "ERROR")

    def run(self):
        self.load_checkpoints()

        while True:
            resp = self.r.xread(self.last_ids, count=500, block=BLOCK_MS)

            if resp:
                for stream_name, messages in resp:
                    if stream_name == STREAM:
                        print(get_ts(), "nof messages:", len(messages))
                        for msg_id, data in messages:
                            self.buffer.append((msg_id, data))
                    elif stream_name == ADMIN_STREAM:
                        self.process_admin_messages(messages)
                    else:
                        print("unknown stream_name:", stream_name)

            self.flush()

if __name__ == "__main__":
    sqlite3_db_fn = sys.argv[1]
    print(get_ts(), "db file:", sqlite3_db_fn)
    worker = StreamToSqlite3(sqlite3_db_fn)
    worker.run()
