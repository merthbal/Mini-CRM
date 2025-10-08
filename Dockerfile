FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.1

RUN pip install --no-cache-dir -r requirements.txt

RUN python - <<'PY'
import importlib, sys, subprocess
try:
    importlib.import_module("alembic")
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "alembic==1.13.2"])
PY

COPY . .
ENV PYTHONPATH=/app

# while building cache the model 
ARG MODEL_NAME=t5-small
ENV MODEL_NAME=${MODEL_NAME}
RUN python - <<'PY'
import os
from transformers import pipeline
m = os.environ.get("MODEL_NAME", "t5-small")
pipeline("summarization", model=m, tokenizer=m)
print("model cached:", m)
PY

# ---- Web ----
FROM base AS web
#CMD ["sh","-lc","alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["bash", "-lc", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# ---- Worker ----
FROM base AS worker
CMD ["python","-m","app.workers.worker"]

