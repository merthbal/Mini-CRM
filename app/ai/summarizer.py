from __future__ import annotations

from typing import Optional
import threading

from transformers import pipeline
from ..settings import get_settings

_settings = get_settings()

# Lazy, thread-safe singleton
_summarizer = None
_lock = threading.Lock()


def _load():
    global _summarizer
    if _summarizer is None:
        with _lock:
            if _summarizer is None:
                _summarizer = pipeline(
                    "summarization",
                    model=_settings.MODEL_NAME,
                    tokenizer=_settings.MODEL_NAME,
                )
    return _summarizer


# RQ job target
# app/ai/summarizer.py
def summarize_text(text: str, max_tokens: int | None = None) -> str:
    sm = _load()
    text = text.strip()
    if not text:
        return ""
    max_len = max_tokens or _settings.SUMMARY_MAX_TOKENS
    # çok kısa inputlarda makul bir üst sınır:
    max_len = max(24, min(max_len, int(len(text.split()) * 0.8)))
    result = sm(text, max_length=max_len, min_length=min(
        16, max_len // 2), do_sample=False)
    return result[0]["summary_text"]
