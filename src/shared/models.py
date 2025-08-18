"""
Shared database models for the Insurance AI Agent system.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from .config import settings

Base = declarative_base()


class ProcessingRecord(Base):
    """Master table for tracking processing records."""
    __tablename__ = "processing_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    unique_processing_id = Column(String(255), unique=True, nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # 'email' or 'file'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Email specific fields
    email_file_uri = Column(String(500))
    email_from = Column(String(255))
    email_to = Column(Text)
    email_cc = Column(Text)
    email_subject = Column(String(500))
    email_body = Column(Text)
    email_date = Column(DateTime)
    num_attachments = Column(Integer, default=0)
    
    # File specific fields
    filename = Column(String(255))
    file_uri = Column(String(500))
    file_size = Column(Integer)
    
    # Relationships
    attachments = relationship("AttachmentRecord", back_populates="processing_record")
    ocr_results = relationship("OCRResult", back_populates="processing_record")


class AttachmentRecord(Base):
    """Child table for storing attachment metadata."""
    __tablename__ = "attachment_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    processing_record_id = Column(Integer, ForeignKey("processing_records.id"), nullable=False)
    attachment_filename = Column(String(255), nullable=False)
    attachment_uri = Column(String(500), nullable=False)
    attachment_size = Column(Integer)
    mime_type = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    processing_record = relationship("ProcessingRecord", back_populates="attachments")


class OCRResult(Base):
    """Table for storing OCR/text extraction results."""
    __tablename__ = "ocr_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    processing_record_id = Column(Integer, ForeignKey("processing_records.id"), nullable=False)
    file_uri = Column(String(500), nullable=False)
    extracted_text = Column(Text)
    confidence_score = Column(String(10))
    page_count = Column(Integer)
    processing_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, completed, failed
    
    # Relationship
    processing_record = relationship("ProcessingRecord", back_populates="ocr_results")


class DocumentClassification(Base):
    """Table for storing AI document classification results."""
    __tablename__ = "document_classifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    processing_record_id = Column(Integer, ForeignKey("processing_records.id"), nullable=False)
    file_uri = Column(String(500), nullable=False)
    document_type = Column(String(100))
    classification_confidence = Column(String(10))
    extracted_entities = Column(Text)  # JSON string of extracted entities
    risk_assessment = Column(String(50))
    priority_level = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    processing_record = relationship("ProcessingRecord")


# Database engine and session setup
def get_engine():
    """Create and return database engine."""
    return create_engine(settings.database_url)


def get_session():
    """Create and return database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables():
    """Create all tables in the database."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
