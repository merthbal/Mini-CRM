# app/workers/tasks.py
from app.database import SessionLocal
from app.models import Node, NoteStatus
from app.ai.summarizer import summarize_text


def run_summarize(text: str, node_id: int) -> str:
    db = SessionLocal()
    try:
        n = db.get(Node, node_id)
        if not n:
            return ""
        n.status = NoteStatus.PROCESSING
        db.commit()

        summary = summarize_text(text)
        n.summary = summary or ""
        n.status = NoteStatus.DONE
        db.commit()
        return summary or ""
    except Exception:
        n = db.get(Node, node_id) if 'n' in locals() else None
        if n:
            n.status = NoteStatus.FAILED
            db.commit()
        raise
    finally:
        db.close()
