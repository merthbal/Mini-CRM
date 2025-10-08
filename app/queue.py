# app/queue.py
import redis
from rq import Queue
from rq.job import Job
from .settings import get_settings

settings = get_settings()

QUEUE_NAME = "ai-queue"
redis_conn = redis.from_url(settings.REDIS_URL)
q = Queue(QUEUE_NAME, connection=redis_conn)


def enqueue(func_path: str, *args, **kwargs) -> Job:
    return q.enqueue(func_path, *args, **kwargs)


def fetch_job(job_id: str) -> Job | None:
    try:
        return Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return None
