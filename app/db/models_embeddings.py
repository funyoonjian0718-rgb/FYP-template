"""Embedding storage model for MySQL-based vector storage."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# actually to speed up the search of the infomration will retrieve only specific keyword 
class Embedding(Base):
    """Store document chunks and their embeddings."""
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(256), nullable=False)  # e.g., "kb_mdg2020.md"
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-serialized vector
    
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_source", "source"),
    )
