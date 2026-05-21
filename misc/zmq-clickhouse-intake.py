import json
import time
import zmq
from clickhouse_driver import Client

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
    
buffer = []
last_flush = time.time()

def flush():
    global buffer, last_flush

    if not buffer:
        return

    # ClickHouse native bulk insert
    #print("insert", buffer)
    ch.execute("INSERT INTO series (series_id, run_serial_num, timestamp, value) VALUES", buffer)
    print(f"Inserted batch: {len(buffer)} rows")

    buffer = []
    last_flush = time.time()

    
if __name__ == "__main__":
    ch = Client(host="localhost", port=9000, user="default", password="", database="default")
    create_all_tables(ch)
    
    ctx = zmq.Context()
    sub_sock = ctx.socket(zmq.SUB)
    sub_sock.bind("tcp://*:5555")
    sub_sock.setsockopt_string(zmq.SUBSCRIBE, "")

    rep_sock = ctx.socket(zmq.REP)
    rep_sock.bind("tcp://*:5556")

    # ---------------------------
    # Main loop
    # ---------------------------
    poller = zmq.Poller()
    poller.register(sub_sock, zmq.POLLIN)
    poller.register(rep_sock, zmq.POLLIN)
    
    print("ZMQ → ClickHouse ingestion started")
    BATCH_SIZE = 10000
    FLUSH_INTERVAL_SEC = 2.0
    
    while True:        
        try:
            events = dict(poller.poll(FLUSH_INTERVAL_SEC * 1000.0))
            if sub_sock in events:
                msg = sub_sock.recv_json()
                #print("sub msg >>>:", msg)
                row = (
                    msg["series_id"],
                    msg["run_serial_num"],
                    msg["timestamp"] if msg["timestamp"] is not None else -1.0,
                    float(msg["value"])
                )
                buffer.append(row)
                
            if rep_sock in events:
                msg = rep_sock.recv_json()
                print("rep msg >>>:", msg)
                action = msg.get("action")
                if action == "save_run_dets":
                    row = (msg["run_id"], 0.0, msg["host"], msg["pid"], msg["argv0"], " ".join(msg["args"]))
                    ch.execute("insert into runs_dets(run_id, created_ts, host, pid, argv0, args) values", [row])
                    reply = {"OK": 1}
                    rep_sock.send_json(reply)
                elif action == "save_series_dets":
                    row = (msg["series_id"], msg["run_id"], msg["key"])
                    ch.execute("insert into series_dets(series_id, run_id, key) values", [row])
                    reply = {"OK": 1}
                    rep_sock.send_json(reply)
                    
            
            # flush conditions
            if len(buffer) >= BATCH_SIZE:
                flush()
            elif time.time() - last_flush > FLUSH_INTERVAL_SEC:
                flush()
                
        except KeyboardInterrupt:
            print("keyboard interrupt")
            break

        except Exception as e:
            print("Error:", e)

    flush()
