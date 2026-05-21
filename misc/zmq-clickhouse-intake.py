import json
import time
import zmq
from clickhouse_driver import Client


# ---------------------------
# ClickHouse connection (native TCP)
# ---------------------------
ch = Client(
    host="localhost",
    port=9000,
    user="default",
    password="",   # explicitly empty
    database="default"
)

# ---------------------------
# Ensure table exists
# ---------------------------
ch.execute("""
CREATE TABLE IF NOT EXISTS telemetry
(
    group_key String,
    key String,
    global_serial_num Int64,
    serial_num Int64,
    timestamp Float64,
    value Float64
)
ENGINE = MergeTree
ORDER BY (group_key, global_serial_num, timestamp)
""")


# ---------------------------
# ZeroMQ setup (SUB socket)
# ---------------------------
ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)

sock.connect("tcp://localhost:5555")
sock.setsockopt_string(zmq.SUBSCRIBE, "")


# ---------------------------
# Batch buffer (IMPORTANT for ClickHouse)
# ---------------------------
BATCH_SIZE = 10000
FLUSH_INTERVAL_SEC = 2.0

buffer = []
last_flush = time.time()


def flush():
    global buffer, last_flush

    if not buffer:
        return

    # ClickHouse native bulk insert
    #print("insert", buffer)
    ch.execute("INSERT INTO telemetry (group_key, key, global_serial_num, serial_num, timestamp, value) VALUES", buffer)
    print(f"Inserted batch: {len(buffer)} rows")

    buffer = []
    last_flush = time.time()


# ---------------------------
# Main loop
# ---------------------------
print("ZMQ → ClickHouse ingestion started")

while True:
    try:
        msg = sock.recv_string()
        #print("msg:", msg)
        data = json.loads(msg)

        row = (
            data["group_key"],
            data["key"],
            data["global_serial_num"],
            data["serial_num"],
            data["timestamp"] if data["timestamp"] is not None else -1.0,
            float(data["value"])
        )

        buffer.append(row)

        # flush conditions
        if len(buffer) >= BATCH_SIZE:
            flush()

        elif time.time() - last_flush > FLUSH_INTERVAL_SEC:
            flush()

    except KeyboardInterrupt:
        break

    except Exception as e:
        print("Error:", e)


flush()
