import zmq

ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect("tcp://localhost:5555")
sock.setsockopt_string(zmq.SUBSCRIBE, "")

while True:
    key_value = sock.recv()
    print(key_value, type(key_value))
