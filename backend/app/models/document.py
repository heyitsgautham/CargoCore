import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class LogisticsDocument(Base):
    __tablename__ = "logistics_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)  # 'VEHICLE' or 'DRIVER'
    entity_id = Column(String(50), nullable=False)    # e.g. 'VH-8922' or 'DRV-1330'
    hub_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True) # Optional hub reference
    
    doc_type = Column(String(100), nullable=False)    # 'CDL', 'Insurance Policy', 'Registration'
    document_url = Column(String, nullable=True)      # URL or Base64 content
    
    status = Column(String(50), default="Pending Verification", nullable=False) # 'Pending Verification', 'Active', 'Rejected', 'Expiring Soon'
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)             # Rejection reason or internal notes

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
