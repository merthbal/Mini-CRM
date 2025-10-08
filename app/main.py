from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .workers.tasks import run_summarize
from .database import init_db, SessionLocal
from .schemas import NodeCreate, NodeUpdate, NodeOut, JobEnqueueOut, JobStatusOut
from .models import Node, User, Role, NoteStatus
from .deps import get_db, get_current_user
from .queue import enqueue, fetch_job
from .auth import router as auth_router, hash_password
from .settings import get_settings

app = FastAPI(title="Mini CRM AI")
app.include_router(auth_router)


def _ensure_admin():
    """ENV'deki ADMIN_EMAIL'e göre admini garanti eder."""
    s = get_settings()
    if not s.ADMIN_EMAIL:
        return  # opsiyonel – tanımlı değilse geç
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(email=s.ADMIN_EMAIL).first()
        if not u:
            pw = s.ADMIN_PASSWORD or "change-me-now"
            u = User(
                email=s.ADMIN_EMAIL,
                password_hash=hash_password(pw),
                role=Role.ADMIN,
            )
            db.add(u)
            db.commit()
        else:
            # varsa da rolünü ADMIN yap (idempotent)
            if u.role != Role.ADMIN:
                u.role = Role.ADMIN
                db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()
    _ensure_admin()


# ---------- Helpers ----------
def _is_admin(user: User) -> bool:
    try:
        return user.role == Role.ADMIN
    except Exception:
        return str(user.role) == "ADMIN"


def _owned_or_admin(db: Session, current: User, node_id: int) -> Node:
    q = db.query(Node).filter(Node.id == node_id)
    if not _is_admin(current):
        q = q.filter(Node.owner_id == current.id)
    n = q.first()
    if not n:
        raise HTTPException(404, "Node not found")
    return n


# ---------- Nodes CRUD ----------
@app.get("/nodes", response_model=List[NodeOut])
def list_nodes(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    q = db.query(Node)
    if not _is_admin(current):
        q = q.filter(Node.owner_id == current.id)
    return q.order_by(Node.id.desc()).all()


@app.post("/nodes", response_model=NodeOut)
def create_node(
    data: NodeCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    n = Node(owner_id=current.id, **data.dict())
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


@app.get("/nodes/{node_id}", response_model=NodeOut)
def get_node(
    node_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return _owned_or_admin(db, current, node_id)


@app.patch("/nodes/{node_id}", response_model=NodeOut)
def update_node(
    node_id: int,
    data: NodeUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    n = _owned_or_admin(db, current, node_id)
    for k, v in data.dict(exclude_unset=True).items():
        setattr(n, k, v)
    db.commit()
    db.refresh(n)
    return n


@app.delete("/nodes/{node_id}")
def delete_node(
    node_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    n = _owned_or_admin(db, current, node_id)
    db.delete(n)
    db.commit()
    return {"ok": True}


# ---------- Summarization ----------
@app.post("/nodes/{node_id}/summarize", response_model=JobEnqueueOut)
def summarize_node(
    node_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    n = _owned_or_admin(db, current, node_id)

    if n.status in (NoteStatus.QUEUED, NoteStatus.PROCESSING):
        raise HTTPException(409, detail="Summarization already in progress")

    # QUEUED
    n.status = NoteStatus.QUEUED
    db.commit()

    # Callable ile enqueue
    job = enqueue(
        run_summarize,
        n.notes,
        node_id=n.id,
        job_timeout=300,
    )
    return JobEnqueueOut(job_id=job.get_id())


@app.get("/jobs/{job_id}", response_model=JobStatusOut)
def job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    job = fetch_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")

    status = job.get_status(refresh=True)
    result = job.result if status == "finished" else None
    return JobStatusOut(job_id=job_id, status=status, result=result)
