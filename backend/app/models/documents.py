from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from ..models.base import Base

class RawItem(Base):
    __tablename__ = "raw_items"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)          # "newsapi", "alphavantage", "upload"
    external_id = Column(String, nullable=True)      # url, symbol+date, filename hash
    title = Column(String, nullable=True)
    url = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    content_text = Column(Text, nullable=True)       # extracted text (for uploads/news)
    raw_json = Column(JSON, nullable=True)           # full payload (keep it!)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
    )

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)            # e.g., "news_top_headlines"
    status = Column(String, nullable=False, default="running")  # running/success/failure
    detail = Column(Text, nullable=True)             # error detail or count summary
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)