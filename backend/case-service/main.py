from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import httpx
from models import Base, TestCase, TestSuite, TestData, RecordingSession
import json

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test_cases.db')
if DATABASE_URL.startswith('postgresql://'):
    # 如果配置的是PostgreSQL，转换为SQLite
    DATABASE_URL = 'sqlite:///./test_cases.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite://') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Case Management Service")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic模型
class TestCaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    assertions: Optional[List[Dict[str, Any]]] = None
    variables: Optional[Dict[str, Any]] = None

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    assertions: Optional[List[Dict[str, Any]]] = None
    variables: Optional[Dict[str, Any]] = None

class RecordingCreate(BaseModel):
    session_id: str
    url: str
    actions: List[Dict[str, Any]]

class RecordingUpdate(BaseModel):
    actions: List[Dict[str, Any]]
    status: Optional[str] = None

class AIGenerateRequest(BaseModel):
    session_id: str

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "case-service"}

# 测试用例CRUD
@app.get("/api/cases")
async def list_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cases = db.query(TestCase).offset(skip).limit(limit).all()
    return [
        {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "steps": json.loads(case.steps) if case.steps else [],
            "assertions": json.loads(case.assertions) if case.assertions and case.assertions != "null" else None,
            "variables": json.loads(case.variables) if case.variables and case.variables != "{}" else None,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "updated_at": case.updated_at.isoformat() if case.updated_at else None
        }
        for case in cases
    ]

@app.get("/api/cases/{case_id}")
async def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "steps": case.steps,
        "assertions": case.assertions,
        "variables": case.variables,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None
    }

@app.post("/api/cases")
async def create_case(case: TestCaseCreate, db: Session = Depends(get_db)):
    db_case = TestCase(
        name=case.name,
        description=case.description,
        steps=json.dumps(case.steps) if case.steps else "[]",
        assertions=json.dumps(case.assertions) if case.assertions else "null",
        variables=json.dumps(case.variables) if case.variables else "{}"
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return {"id": db_case.id, "message": "Test case created successfully"}

@app.put("/api/cases/{case_id}")
async def update_case(case_id: int, case: TestCaseUpdate, db: Session = Depends(get_db)):
    db_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    if case.name is not None:
        db_case.name = case.name
    if case.description is not None:
        db_case.description = case.description
    if case.steps is not None:
        db_case.steps = json.dumps(case.steps) if isinstance(case.steps, (dict, list)) else case.steps
    if case.assertions is not None:
        db_case.assertions = json.dumps(case.assertions) if case.assertions else "null"
    if case.variables is not None:
        db_case.variables = json.dumps(case.variables) if case.variables else "{}"
    
    db.commit()
    return {"message": "Test case updated successfully"}

@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: int, db: Session = Depends(get_db)):
    db_case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    db.delete(db_case)
    db.commit()
    return {"message": "Test case deleted successfully"}

# 录制会话管理
@app.post("/api/cases/recordings")
async def create_recording(recording: RecordingCreate, db: Session = Depends(get_db)):
    db_recording = RecordingSession(
        session_id=recording.session_id,
        url=recording.url,
        actions=json.dumps(recording.actions),
        status='recording'
    )
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    return {"id": db_recording.id, "session_id": db_recording.session_id}

@app.put("/api/cases/recordings/{session_id}")
async def update_recording(session_id: str, recording: RecordingUpdate, db: Session = Depends(get_db)):
    db_recording = db.query(RecordingSession).filter(RecordingSession.session_id == session_id).first()
    if not db_recording:
        raise HTTPException(status_code=404, detail="Recording session not found")
    
    db_recording.actions = json.dumps(recording.actions)
    if recording.status:
        db_recording.status = recording.status
    
    db.commit()
    return {"message": "Recording updated successfully"}

@app.get("/api/cases/recordings/{session_id}")
async def get_recording(session_id: str, db: Session = Depends(get_db)):
    recording = db.query(RecordingSession).filter(RecordingSession.session_id == session_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording session not found")
    
    return {
        "id": recording.id,
        "session_id": recording.session_id,
        "url": recording.url,
        "actions": json.loads(recording.actions) if recording.actions else [],
        "status": recording.status,
        "created_at": recording.created_at.isoformat() if recording.created_at else None
    }

# AI生成测试用例
@app.post("/api/cases/generate")
async def generate_test_case(request: AIGenerateRequest, db: Session = Depends(get_db)):
    # 获取录制会话
    recording = db.query(RecordingSession).filter(RecordingSession.session_id == request.session_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording session not found")
    
    # 调用AI服务生成测试用例
    ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:8003')
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ai_service_url}/api/ai/generate-case",
                json={
                    "url": recording.url,
                    "actions": recording.actions
                }
            )
            response.raise_for_status()
            generated_case = response.json()
        
        # 创建测试用例
        db_case = TestCase(
            name=generated_case.get('name', 'AI生成的测试用例'),
            description=generated_case.get('description', ''),
            steps=generated_case.get('steps', recording.actions),
            assertions=generated_case.get('assertions', []),
            variables=generated_case.get('variables', {})
        )
        db.add(db_case)
        
        # 更新录制状态
        recording.status = 'completed'
        
        db.commit()
        db.refresh(db_case)
        
        return {
            "id": db_case.id,
            "name": db_case.name,
            "message": "Test case generated successfully"
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
