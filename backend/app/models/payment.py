import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OrderPayment(Base):
    """
    Ledger of every payment event for an order.
    One row per payment action (online, COD, partial, top-up, refund).
    """
    __tablename__ = "order_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The Razorpay dummy pay_XXXX id for online, or a generated ref for COD
    payment_ref: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)   # ONLINE | COD | PARTIAL
    payment_method: Mapped[str | None] = mapped_column(String(100), nullable=True)  # UPI, Card, etc.
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    # driver user_id when COD collected by driver
    collected_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
