import json
import zmq
import uuid, os, socket, sys

ZMQ_PUB_ENDPOINT = "tcp://localhost:5555"
ZMQ_REQ_ENDPOINT = "tcp://localhost:5556"

_ctx = None
_pub_socket = None
_req_socket = None

def _get_pub_socket():
    global _ctx, _pub_socket
    if _ctx is None:
        _ctx = zmq.Context.instance()
    if _pub_socket is None:
        _pub_socket = _ctx.socket(zmq.PUB)
        _pub_socket.connect(ZMQ_PUB_ENDPOINT)
    return _pub_socket

def _get_req_socket():
    global _ctx, _req_socket
    if _ctx is None:
        _ctx = zmq.Context.instance()        
    if _req_socket is None:
        _req_socket = _ctx.socket(zmq.REQ)
        _req_socket.connect(ZMQ_REQ_ENDPOINT)
        _req_socket.setsockopt(zmq.RCVTIMEO, 5000) # timeout 5 secs

    return _req_socket
    
def _send(payload):
    sock = _get_pub_socket()
    sock.send_multipart([json.dumps(payload).encode("utf-8")])

def _send_with_response(payload):
    sock = _get_req_socket()
    sock.send_json(payload)
    reply = sock.recv_json()
    return reply
    
run_id = str(uuid.uuid4())
series_ids = {} # key => series_id
run_serial_num = 0

def save_run_dets():
    global run_id
    host = socket.gethostname()
    pid = os.getpid()
    print(f"process {pid}@{host} starting with run_id {run_id}")
    msg = {"action": "save_run_dets", "run_id": run_id, "host": host, "pid": pid, "argv0": sys.executable, "args": sys.argv}
    print("<<< msg:", msg)
    msg_response = _send_with_response(msg)
    print(">>> msg_response:", msg_response)

def save_series_dets(series_id, run_id, key):
    msg = {"action": "save_series_dets", "series_id": series_id, "run_id": run_id, "key": key}
    print("<<< msg:", msg)
    msg_response = _send_with_response(msg)
    print(">>> msg_response:", msg_response)    
    
def get_series_id(key:str) -> tuple[bool, str]:
    if key in series_ids:
        return False, series_ids.get(key)    
    global run_id
    new_series_id = run_id + "---" + str(hash(key))
    series_ids[key] = new_series_id
    return True, new_series_id

def add_serial_point(key, value):
    add_ts_point(key, None, value)

def add_ts_point(key, ts, value):
    is_new_key, series_id = get_series_id(key)
    if is_new_key:
        save_series_dets(series_id, run_id, key)
    global run_serial_num
    run_serial_num += 1
    _send({"series_id": series_id, "run_serial_num": run_serial_num, "timestamp": ts, "value": float(value)})    
