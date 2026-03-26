import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from models.database import Base


class JSONBType(TypeDecorator):
    """A type that uses JSONB on PostgreSQL and JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class ResourceStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class ProcessingStatus(enum.Enum):
    """Processing status for resource content analysis and enrichment."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String, nullable=False)
    original_content = Column(Text, nullable=False)
    prefer_provider = Column(String, nullable=True)
    title = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(JSONBType, nullable=True, default=list)
    status = Column(
        Enum(ResourceStatus), default=ResourceStatus.PENDING, nullable=False
    )
    status_message = Column(String, nullable=True)
    fetch_tier = Column(String(20), nullable=True)  # 'api', 'http', 'playwright'
    fetch_error_type = Column(String(30), nullable=True)  # Error classification
    processing_status = Column(
        Enum(ProcessingStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProcessingStatus.PENDING,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="resources")
