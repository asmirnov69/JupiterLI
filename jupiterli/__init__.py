import json
import zmq

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


def _send(key, payload):
    sock = _get_pub_socket()
    sock.send_multipart([key.encode("utf-8"), json.dumps(payload).encode("utf-8")])


def add_serial_point(key, value):
    _send(key, {"value": float(value)})


def add_ts_point(key, ts, value):
    _send(key, {"timestamp": ts, "value": value})
