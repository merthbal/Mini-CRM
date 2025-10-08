# ---- Base ----
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# 1) Python bağımlılıkları (önce requirements cache’i)
COPY requirements.txt .

# CPU için PyTorch (özetleme CPU’da koşacak)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.1

# Geri kalan paketler
RUN pip install --no-cache-dir -r requirements.txt

# Alembic requirements.txt'de yoksa güvenlik ağı olarak kur
RUN python - <<'PY'
import importlib, sys, subprocess
try:
    importlib.import_module("alembic")
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "alembic==1.13.2"])
PY

# 2) Uygulama dosyaları (alebmic.ini ve alembic/ DAHİL bütün repo kökü)
COPY . .
ENV PYTHONPATH=/app

# (Opsiyonel) Modeli build sırasında cache’le ki container ilk açılışta beklemesin
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
# app başlamadan önce migration uygula, sonra uvicorn’u başlat
CMD ["sh","-lc","alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

# ---- Worker ----
FROM base AS worker
CMD ["python","-m","app.workers.worker"]
