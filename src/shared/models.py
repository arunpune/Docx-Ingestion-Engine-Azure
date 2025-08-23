"""
Database Models for Insurance AI Agent System
=============================================
Author: Utsav Pat

This module defines the SQLAlchemy database models for the Insurance AI Agent system.
It provides a comprehensive data structure for tracking email processing, document analysis,
OCR results, and document classification throughout the entire pipeline.

Database Schema Overview:
- ProcessingRecord: Master table for tracking all processing operations
- AttachmentRecord: Child table for email attachment metadata
- OCRResult: Stores text extraction results from documents
- DocumentClassification: Stores AI classification results

Key Features:
- Complete audit trail for all document processing
- Relationship management between related records
- Automated timestamp tracking for created/updated records
- Support for both email and file upload processing modes
- Flexible status tracking throughout the processing pipeline

Author: Insurance AI Agent Team
Version: 1.0
Dependencies: sqlalchemy, datetime
"""

# Standard library imports
from datetime import datetime  # Date and time handling for timestamps
from typing import Optional, List  # Type hints for better code documentation

# SQLAlchemy imports for database ORM
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base  # Base class for model definitions
from sqlalchemy.orm import relationship, sessionmaker    # Relationship management and sessions
from sqlalchemy import create_engine                     # Database engine creation

# Local configuration import
from .config import settings  # Application settings and configuration

# Create the base class for all database models
Base = declarative_base()


class ProcessingRecord(Base):
    """
    Master table for tracking all document processing operations.
    
    This is the primary table that tracks every processing operation in the system,
    whether initiated by email or file upload. It maintains comprehensive metadata
    about the source, processing status, and relationships to child records.
    
    Attributes:
        id (int): Primary key auto-incrementing identifier
        unique_processing_id (str): Unique UUID for external reference
        source_type (str): Type of processing source ('email' or 'file')
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last modification timestamp
        status (str): Current processing status
        
    Email-specific attributes:
        email_file_uri (str): Azure Blob Storage URI for email file
        email_from (str): Sender email address
        email_to (str): Recipient email addresses
        email_cc (str): CC email addresses
        email_subject (str): Email subject line
        email_body (str): Email body content
        email_date (datetime): Email sent/received date
        num_attachments (int): Number of email attachments
        
    File-specific attributes:
        filename (str): Original uploaded filename
        file_uri (str): Azure Blob Storage URI for uploaded file
        file_size (int): File size in bytes
        
    Relationships:
        attachments: Related AttachmentRecord objects
        ocr_results: Related OCRResult objects
    """
    __tablename__ = "processing_records"
    
    # Primary key and unique identifier
    id = Column(Integer, primary_key=True, autoincrement=True)
    unique_processing_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Processing metadata
    source_type = Column(String(50), nullable=False)  # 'email' or 'file'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Email-specific fields for email processing mode
    email_file_uri = Column(String(500))    # Blob storage URI for email file
    email_from = Column(String(255))        # Sender email address
    email_to = Column(Text)                 # Recipient email addresses (JSON array)
    email_cc = Column(Text)                 # CC email addresses (JSON array)
    email_subject = Column(String(500))     # Email subject line
    email_body = Column(Text)               # Email body content
    email_date = Column(DateTime)           # Email timestamp
    num_attachments = Column(Integer, default=0)  # Count of email attachments
    
    # File-specific fields for direct file upload mode
    filename = Column(String(255))          # Original filename
    file_uri = Column(String(500))          # Blob storage URI for file
    file_size = Column(Integer)             # File size in bytes
    
    # Database relationships to child tables
    attachments = relationship("AttachmentRecord", back_populates="processing_record")
    ocr_results = relationship("OCRResult", back_populates="processing_record")


class AttachmentRecord(Base):
    """
    Child table for storing email attachment metadata and processing information.
    
    This table stores detailed information about each email attachment that needs
    to be processed. Each attachment is linked to a parent ProcessingRecord and
    tracks its own processing status and metadata.
    
    Attributes:
        id (int): Primary key auto-incrementing identifier
        processing_record_id (int): Foreign key to parent ProcessingRecord
        attachment_filename (str): Original attachment filename
        attachment_uri (str): Azure Blob Storage URI for attachment file
        attachment_size (int): Attachment file size in bytes
        mime_type (str): MIME type of the attachment
        created_at (datetime): Record creation timestamp
        
    Relationships:
        processing_record: Parent ProcessingRecord object
    """
    __tablename__ = "attachment_records"
    
    # Primary key and foreign key relationship
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
