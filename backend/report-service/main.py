from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
import os
# from minio import Minio
# from minio.error import S3Error
import io
from datetime import datetime
from jinja2 import Template

# 数据库配置
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Report and Evidence Service")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 本地存储配置
STORAGE_DIR = os.getenv('STORAGE_DIR', './storage')
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# 依赖注入
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic模型
class EvidenceUpload(BaseModel):
    run_id: int
    step_id: Optional[int] = None
    type: str
    metadata: Optional[Dict[str, Any]] = None

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "report-service"}

# 上传测试证据
@app.post("/api/reports/evidence")
async def upload_evidence(
    run_id: int,
    step_id: Optional[int] = None,
    evidence_type: str = "screenshot",
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 生成文件路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = os.path.join(STORAGE_DIR, f"run_{run_id}", f"step_{step_id or 0}")
        if not os.path.exists(run_dir):
            os.makedirs(run_dir)
            
        file_name = f"{evidence_type}_{timestamp}_{file.filename}"
        file_path = os.path.join(run_dir, file_name)
        
        # 保存文件
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        # 生成访问URL (相对路径)
        file_url = f"/storage/run_{run_id}/step_{step_id or 0}/{file_name}"
        
        # 保存到数据库
        query = """
            INSERT INTO test_evidence (run_id, step_id, type, file_url, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        
        cursor = db.execute(query, (run_id, step_id, evidence_type, file_url, None))
        evidence_id = cursor.fetchone()[0]
        db.commit()
        
        return {
            "id": evidence_id,
            "file_url": file_url,
            "message": "Evidence uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

# 获取测试证据列表
@app.get("/api/reports/evidence/{run_id}")
async def get_evidence(run_id: int, db: Session = Depends(get_db)):
    query = """
        SELECT id, run_id, step_id, type, file_url, metadata, created_at
        FROM test_evidence
        WHERE run_id = %s
        ORDER BY step_id, created_at
    """
    
    cursor = db.execute(query, (run_id,))
    evidence_list = cursor.fetchall()
    
    return [
        {
            "id": row[0],
            "run_id": row[1],
            "step_id": row[2],
            "type": row[3],
            "file_url": row[4],
            "metadata": row[5],
            "created_at": row[6].isoformat() if row[6] else None
        }
        for row in evidence_list
    ]

# 获取测试运行详情
@app.get("/api/reports/runs/{run_id}")
async def get_test_run(run_id: int, db: Session = Depends(get_db)):
    # 获取运行基本信息
    run_query = """
        SELECT tr.id, tr.case_id, tr.suite_id, tr.status, tr.start_time, tr.end_time, tr.result,
               tc.name as case_name, tc.description as case_description
        FROM test_runs tr
        LEFT JOIN test_cases tc ON tr.case_id = tc.id
        WHERE tr.id = %s
    """
    
    cursor = db.execute(run_query, (run_id,))
    run_row = cursor.fetchone()
    
    if not run_row:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # 获取步骤结果
    steps_query = """
        SELECT id, step_index, step_name, status, error_message, ai_analysis,
               screenshot_url, dom_snapshot_url, execution_time, created_at
        FROM test_step_results
        WHERE run_id = %s
        ORDER BY step_index
    """
    
    cursor = db.execute(steps_query, (run_id,))
    steps = cursor.fetchall()
    
    return {
        "id": run_row[0],
        "case_id": run_row[1],
        "suite_id": run_row[2],
        "status": run_row[3],
        "start_time": run_row[4].isoformat() if run_row[4] else None,
        "end_time": run_row[5].isoformat() if run_row[5] else None,
        "result": run_row[6],
        "case_name": run_row[7],
        "case_description": run_row[8],
        "steps": [
            {
                "id": step[0],
                "step_index": step[1],
                "step_name": step[2],
                "status": step[3],
                "error_message": step[4],
                "ai_analysis": step[5],
                "screenshot_url": step[6],
                "dom_snapshot_url": step[7],
                "execution_time": step[8],
                "created_at": step[9].isoformat() if step[9] else None
            }
            for step in steps
        ]
    }

# 获取测试运行列表
@app.get("/api/reports/runs")
async def list_test_runs(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    where_clause = ""
    params = []
    
    if status:
        where_clause = "WHERE tr.status = %s"
        params.append(status)
    
    query = f"""
        SELECT tr.id, tr.case_id, tr.suite_id, tr.status, tr.start_time, tr.end_time,
               tc.name as case_name
        FROM test_runs tr
        LEFT JOIN test_cases tc ON tr.case_id = tc.id
        {where_clause}
        ORDER BY tr.created_at DESC
        LIMIT %s OFFSET %s
    """
    
    params.extend([limit, skip])
    
    cursor = db.execute(query, tuple(params))
    runs = cursor.fetchall()
    
    return [
        {
            "id": row[0],
            "case_id": row[1],
            "suite_id": row[2],
            "status": row[3],
            "start_time": row[4].isoformat() if row[4] else None,
            "end_time": row[5].isoformat() if row[5] else None,
            "case_name": row[6]
        }
        for row in runs
    ]

# 生成HTML测试报告
@app.get("/api/reports/generate/{run_id}", response_class=HTMLResponse)
async def generate_report(run_id: int, db: Session = Depends(get_db)):
    # 获取测试运行详情
    run_data = await get_test_run(run_id, db)
    
    # HTML模板
    template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试报告 - {{ case_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }
        .summary { background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .summary-item { display: inline-block; margin-right: 30px; }
        .summary-label { font-weight: bold; color: #666; }
        .status-passed { color: #4CAF50; font-weight: bold; }
        .status-failed { color: #f44336; font-weight: bold; }
        .step { border: 1px solid #ddd; margin: 15px 0; padding: 15px; border-radius: 5px; }
        .step-header { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .step-passed { border-left: 4px solid #4CAF50; }
        .step-failed { border-left: 4px solid #f44336; background: #fff5f5; }
        .error-box { background: #ffebee; border: 1px solid #f44336; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .ai-analysis { background: #e3f2fd; border: 1px solid #2196F3; padding: 15px; border-radius: 3px; margin: 10px 0; }
        .screenshot { max-width: 100%; border: 1px solid #ddd; margin: 10px 0; }
        .meta { color: #666; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f5f5f5; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>测试报告</h1>
        
        <div class="summary">
            <div class="summary-item">
                <span class="summary-label">测试用例:</span> {{ case_name }}
            </div>
            <div class="summary-item">
                <span class="summary-label">状态:</span> 
                <span class="status-{{ status }}">{{ status | upper }}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">开始时间:</span> {{ start_time }}
            </div>
            <div class="summary-item">
                <span class="summary-label">结束时间:</span> {{ end_time }}
            </div>
        </div>
        
        <h2>测试步骤</h2>
        
        {% for step in steps %}
        <div class="step step-{{ step.status }}">
            <div class="step-header">
                步骤 {{ step.step_index + 1 }}: {{ step.step_name }}
                <span class="status-{{ step.status }}">[{{ step.status | upper }}]</span>
            </div>
            
            <div class="meta">
                执行时间: {{ step.execution_time }}ms
            </div>
            
            {% if step.error_message %}
            <div class="error-box">
                <strong>错误信息:</strong><br>
                {{ step.error_message }}
            </div>
            {% endif %}
            
            {% if step.ai_analysis %}
            <div class="ai-analysis">
                <strong>🤖 AI分析:</strong><br>
                {{ step.ai_analysis }}
            </div>
            {% endif %}
            
            {% if step.screenshot_url %}
            <details>
                <summary>查看截图</summary>
                <p class="meta">截图路径: {{ step.screenshot_url }}</p>
            </details>
            {% endif %}
        </div>
        {% endfor %}
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; text-align: center;">
            <p>报告生成时间: {{ report_time }}</p>
            <p>AI赋能的网页自动化测试工具</p>
        </div>
    </div>
</body>
</html>
    """
    
    template = Template(template_str)
    html_content = template.render(
        case_name=run_data.get('case_name', 'Unknown'),
        status=run_data.get('status', 'unknown'),
        start_time=run_data.get('start_time', 'N/A'),
        end_time=run_data.get('end_time', 'N/A'),
        steps=run_data.get('steps', []),
        report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    return HTMLResponse(content=html_content)

# 比较两次测试运行
@app.get("/api/reports/compare/{run_id1}/{run_id2}")
async def compare_runs(run_id1: int, run_id2: int, db: Session = Depends(get_db)):
    run1 = await get_test_run(run_id1, db)
    run2 = await get_test_run(run_id2, db)
    
    comparison = {
        "run1": run1,
        "run2": run2,
        "differences": []
    }
    
    # 比较步骤数量
    if len(run1['steps']) != len(run2['steps']):
        comparison['differences'].append({
            "type": "step_count",
            "message": f"步骤数量不同: {len(run1['steps'])} vs {len(run2['steps'])}"
        })
    
    # 比较每个步骤的状态
    for i in range(min(len(run1['steps']), len(run2['steps']))):
        step1 = run1['steps'][i]
        step2 = run2['steps'][i]
        
        if step1['status'] != step2['status']:
            comparison['differences'].append({
                "type": "step_status",
                "step_index": i,
                "step_name": step1['step_name'],
                "run1_status": step1['status'],
                "run2_status": step2['status']
            })
    
    return comparison

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
