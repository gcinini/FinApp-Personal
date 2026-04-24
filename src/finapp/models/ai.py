"""AI interactions and audit log."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finapp.db.base import Base
from finapp.models.mixins import TimestampMixin


class AIInteraction(Base, TimestampMixin):
    __tablename__ = "ai_interaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    feature: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text)
    tokens_in: Mapped[int] = mapped_column(default=0, nullable=False)
    tokens_out: Mapped[int] = mapped_column(default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    linked_entity_type: Mapped[str | None] = mapped_column(String(32))
    linked_entity_id: Mapped[int | None] = mapped_column()


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[int | None] = mapped_column()
    details_json: Mapped[str | None] = mapped_column(Text)
    integrity_hash: Mapped[str | None] = mapped_column(String(64))
