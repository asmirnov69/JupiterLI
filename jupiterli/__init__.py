import json
import zmq
import uuid, os, socket, sys

ZMQ_PUB_ENDPOINT = "tcp://*:5555"

_ctx = None
_pub_socket = None

def _get_pub_socket():
    global _ctx, _pub_socket
    if _pub_socket is None:
        _ctx = zmq.Context.instance()
        _pub_socket = _ctx.socket(zmq.PUB)
        _pub_socket.bind(ZMQ_PUB_ENDPOINT)
    return _pub_socket

def _send(payload):
    sock = _get_pub_socket()
    sock.send_multipart([json.dumps(payload).encode("utf-8")])

group_key = str(uuid.uuid4())
global_serial_num = 0
serial_nums = {}

def dump_run_info():
    global group_key
    host = socket.gethostname()
    pid = os.getpid()
    print(f"process {pid}@{host} starting with group_key {group_key}")
    msg = {"group_key": group_key, "host": host, "pid": pid, "argv0": sys.executable, "args": sys.argv}
    print(msg)
    _send(msg)
    
def add_serial_point(key, value):
    add_ts_point(key, None, value)

def add_ts_point(key, ts, value):
    global serial_nums, global_serial_num, group_key
    if not key in serial_nums:
        serial_nums[key] = 0
    serial_nums[key] += 1
    global_serial_num += 1
    _send({"group_key": group_key, "key": key, "global_serial_num": global_serial_num, "serial_num": serial_nums[key], "timestamp": ts, "value": float(value)})    
