from rq import Connection, Worker
from app.queue import redis_conn, QUEUE_NAME

if __name__ == "__main__":
    with Connection(redis_conn):
        Worker([QUEUE_NAME]).work(with_scheduler=True)
