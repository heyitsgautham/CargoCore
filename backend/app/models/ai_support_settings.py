import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AISupportSettings(Base):
    __tablename__ = "ai_support_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    tone: Mapped[str] = mapped_column(String(60), nullable=False, default="Friendly & Empathetic")
    language_mode: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="Auto-Detect (Multilingual)",
    )
    sentiment_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    refund_limit_inr: Mapped[int] = mapped_column(Integer, nullable=False, default=5000)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    autonomous_replies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    legal_threat_detection: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    real_time_sentiment_analysis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    proactive_human_handover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[updated_by_user_id])  # noqa: F821
