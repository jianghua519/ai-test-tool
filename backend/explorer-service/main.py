"""
探索服务 FastAPI 主程序
提供自动网站探索的API接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import os

from explorer import WebExplorer, get_explorer, cleanup_explorer

app = FastAPI(title="Explorer Service")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic模型
class StartExploreRequest(BaseModel):
    url: str
    strategy: str = "mixed"
    max_depth: int = 3
    max_pages: int = 20


class ExploreResponse(BaseModel):
    explore_id: str
    message: str


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "explorer-service"}


@app.post("/api/explore/start", response_model=ExploreResponse)
async def start_exploration(request: StartExploreRequest):
    """启动探索任务"""
    try:
        explorer = get_explorer()

        # 创建新的探索会话
        explore_id = explorer.create_session(
            start_url=request.url,
            strategy=request.strategy
        )

        # 在后台运行探索
        asyncio.create_task(explorer.explore(explore_id))

        return ExploreResponse(
            explore_id=explore_id,
            message="Exploration started"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting exploration: {str(e)}")


@app.get("/api/explore/{explore_id}")
async def get_explore_status(explore_id: str):
    """获取探索状态"""
    try:
        explorer = get_explorer()
        status = await explorer.get_session_status(explore_id)

        # 返回探索统计
        return {
            **status,
            "stats": explorer.state_machine.get_exploration_stats()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@app.get("/api/explore/{explore_id}/results")
async def get_explore_results(explore_id: str):
    """获取探索结果"""
    try:
        explorer = get_explorer()
        results = explorer.get_exploration_results(explore_id)
        return results

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting results: {str(e)}")


@app.post("/api/explore/{explore_id}/pause")
async def pause_exploration(explore_id: str):
    """暂停探索"""
    try:
        explorer = get_explorer()
        await explorer.pause_explore(explore_id)
        return {"message": "Exploration paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing: {str(e)}")


@app.post("/api/explore/{explore_id}/resume")
async def resume_exploration(explore_id: str):
    """恢复探索"""
    try:
        explorer = get_explorer()
        await explorer.resume_explore(explore_id)
        return {"message": "Exploration resumed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming: {str(e)}")


@app.post("/api/explore/{explore_id}/stop")
async def stop_exploration(explore_id: str):
    """停止探索"""
    try:
        explorer = get_explorer()
        await explorer.stop_explore(explore_id)
        return {"message": "Exploration stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping: {str(e)}")


@app.post("/api/explore/{explore_id}/generate-cases")
async def generate_test_cases(explore_id: str):
    """生成测试用例"""
    try:
        explorer = get_explorer()
        result = explorer.generate_test_cases(explore_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating cases: {str(e)}")


@app.get("/api/explore/{explore_id}/coverage")
async def get_coverage_report(explore_id: str):
    """获取覆盖度报告"""
    try:
        explorer = get_explorer()
        report = explorer.generate_coverage_report(explore_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting coverage: {str(e)}")


# 优雅关闭
@app.on_event("shutdown")
async def shutdown_event():
    await cleanup_explorer()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
