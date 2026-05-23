import time
import redis, json
import clickhouse_driver

STREAM = "telemetry"
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
    run_id String,
    created_ts Float64, host String, pid Int64,
    argv0 String, args String
    ) ENGINE = MergeTree ORDER BY (run_id)
    """)
    
    qs.append("""
    create table if not exists series_dets (
    series_id String,
    run_id String,
    key String
    ) ENGINE = MergeTree ORDER BY (series_id)
    """)

    qs.append("""
    create table if not exists series (
    series_id String,
    run_serial_num Int64,
    timestamp Float64,
    value Float64
    ) ENGINE = MergeTree ORDER BY (series_id, run_serial_num)
    """)

    for q in qs:
        print(q)
        ch.execute(q)


class StreamToClickHouse:

    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        self.ch = clickhouse_driver.Client(host="localhost", user="default", password="", database = "default")
        create_all_tables(self.ch)
        self.buffer = []

    def ensure_group(self):
        try:
            self.r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        except redis.exceptions.ResponseError:
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

        # 1. Insert into ClickHouse
        cols = ",".join(list(data.keys()))
        self.ch.execute(f"insert into series({cols}) values", rows)

        # 2. ACK only after successful insert
        if msg_ids:
            self.r.xack(STREAM, GROUP, *msg_ids)

    def run(self):
        self.ensure_group()

        while True:
            resp = self.r.xreadgroup(GROUP, CONSUMER, {STREAM: ">"}, count=500, block=BLOCK_MS)

            if resp:
                for _, messages in resp:
                    for msg_id, data in messages:
                        self.buffer.append((msg_id, data))

            # flush by size
            if len(self.buffer) >= BATCH_SIZE:
                self.flush()
            elif time.time() - last_flush > FLUSH_INTERVAL_SEC:
                self.flush()

            # optional periodic flush (low latency)
            else:
                time.sleep(0.01)


if __name__ == "__main__":
    worker = StreamToClickHouse()
    worker.run()
