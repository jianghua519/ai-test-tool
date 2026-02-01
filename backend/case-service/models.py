from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class TestCase(Base):
    __tablename__ = 'test_cases'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(JSONB, nullable=False)
    assertions = Column(JSONB)
    variables = Column(JSONB)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class TestSuite(Base):
    __tablename__ = 'test_suites'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    case_ids = Column(ARRAY(Integer))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class TestData(Base):
    __tablename__ = 'test_data'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class RecordingSession(Base):
    __tablename__ = 'recording_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    actions = Column(JSONB, nullable=False)
    status = Column(String(50), default='recording')
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
