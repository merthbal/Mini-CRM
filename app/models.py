from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Text, ForeignKey, DateTime, func,
    Enum as SAEnum, Index
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

Base = declarative_base()

# --- Enums ---


class Role(str, Enum):
    ADMIN = "ADMIN"
    AGENT = "AGENT"


class NoteStatus(str, Enum):
    NEW = "new"
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

# --- Models ---


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="user_role"),
        default=Role.AGENT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    nodes: Mapped[List["Node"]] = relationship(
        "Node", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    type: Mapped[Optional[str]] = mapped_column(String(50), default="lead")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[NoteStatus] = mapped_column(
        SAEnum(NoteStatus, name="note_status"),
        default=NoteStatus.NEW, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, default="")
    summary: Mapped[Optional[str]] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped[User] = relationship("User", back_populates="nodes")

    # Faydalı birleşik indeks örneği (sorguları hızlandırır)
    __table_args__ = (
        Index("ix_nodes_owner_status", "owner_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Node id={self.id} owner_id={self.owner_id} status={self.status}>"
