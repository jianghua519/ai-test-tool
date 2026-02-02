from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ARRAY, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import json

Base = declarative_base()

# SQLite兼容的JSON类型
try:
    # 检查是否是SQLite数据库
    from sqlalchemy.dialects.sqlite import SQLiteDialect
    class SQLiteJSONType:
        def bind_processor(self, dialect):
            def process(value):
                if value is None:
                    return None
                return json.dumps(value)
            return process
        
        def result_processor(self, dialect):
            def process(value):
                if value is None:
                    return None
                return json.loads(value)
            return process
except ImportError:
    SQLiteJSONType = JSON

class TestCase(Base):
    __tablename__ = 'test_cases'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    steps = Column(Text, nullable=False)  # SQLite compatible
    assertions = Column(Text)
    variables = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class TestSuite(Base):
    __tablename__ = 'test_suites'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    case_ids = Column(Text)  # SQLite compatible, store as JSON array
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class TestData(Base):
    __tablename__ = 'test_data'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    data = Column(Text, nullable=False)  # SQLite compatible
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

class RecordingSession(Base):
    __tablename__ = 'recording_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    actions = Column(Text, nullable=False)  # SQLite compatible
    status = Column(String(50), default='recording')
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
