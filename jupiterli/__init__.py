import redis

REDIS_URL = "redis://localhost"
redis_conn = redis.from_url(REDIS_URL, decode_responses=True)

def add_ts_point(key, ts, value):
    global redis_conn
    redis_conn.xadd(key, {"timestamp": ts, "value": value}, maxlen = 10000)
    
