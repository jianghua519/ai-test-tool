from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from openai import OpenAI
import httpx
import importlib.util
spec = importlib.util.spec_from_file_location("business_analyzer", "business-analyzer.py")
business_analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(business_analyzer)
BusinessAnalyzer = business_analyzer.BusinessAnalyzer

app = FastAPI(title="AI Service")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
ZAI_API_KEY = os.getenv('ZAI_API_KEY')
ZAI_BASE_URL = os.getenv('ZAI_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/')

# Pydantic模型
class GenerateCaseRequest(BaseModel):
    url: str
    actions: List[Dict[str, Any]]
    model: Optional[str] = "glm-4.5-air"
    provider: Optional[str] = "zai"  # openai, ollama, or zai

class AnalyzeErrorRequest(BaseModel):
    error_message: str
    step_name: str
    selector: str
    screenshot_context: Optional[str] = None
    dom_context: Optional[str] = None
    console_logs: Optional[List[str]] = None
    model: Optional[str] = "glm-4.5-air"
    provider: Optional[str] = "zai"

class AnalyzeBusinessRequest(BaseModel):
    url: str
    description: str
    model: Optional[str] = "glm-4.5-air"
    provider: Optional[str] = "zai"

# LLM网关
class LLMGateway:
    @staticmethod
    async def generate(prompt: str, model: str = "gpt-4.1-mini", provider: str = "openai") -> str:
        if provider == "openai":
            return await LLMGateway._generate_openai(prompt, model)
        elif provider == "ollama":
            return await LLMGateway._generate_ollama(prompt, model)
        elif provider == "zai":
            return await LLMGateway._generate_zai(prompt, model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @staticmethod
    async def _generate_openai(prompt: str, model: str) -> str:
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的自动化测试专家，擅长分析网页操作并生成测试用例。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    
    @staticmethod
    async def _generate_ollama(prompt: str, model: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get('response', '{}')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")
    
    @staticmethod
    async def _generate_zai(prompt: str, model: str) -> str:
        if not ZAI_API_KEY:
            raise HTTPException(status_code=500, detail="ZAI API key not configured")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{ZAI_BASE_URL}chat/completions",
                    headers={
                        "Authorization": f"Bearer {ZAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的自动化测试专家，擅长分析网页操作并生成测试用例。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "response_format": {"type": "json_object"}
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ZAI API error: {str(e)}")

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-service"}

# Few-shot示例
FEW_SHOT_EXAMPLES = [
    {
        "input": {
            "url": "https://example.com/login",
            "actions": [
                {"type": "click", "selector": "#username", "value": "testuser@example.com"},
                {"type": "type", "selector": "#username", "value": "testuser@example.com"},
                {"type": "type", "selector": "#password", "value": "password123"},
                {"type": "click", "selector": "button[type='submit']"}
            ]
        },
        "output": {
            "name": "用户登录测试",
            "description": "验证用户能够使用有效的用户名和密码成功登录系统",
            "steps": [
                {"name": "输入用户名", "action": "type", "selector": "#username", "value": "${{username}}"},
                {"name": "输入密码", "action": "type", "selector": "#password", "value": "${{password}}"},
                {"name": "点击登录按钮", "action": "click", "selector": "button[type='submit']"}
            ],
            "assertions": [
                {"type": "urlContains", "value": "/dashboard", "description": "验证跳转到仪表板页面"},
                {"type": "textVisible", "value": "欢迎", "description": "验证显示欢迎信息"}
            ],
            "variables": {
                "username": "testuser@example.com",
                "password": "password123"
            }
        }
    },
    {
        "input": {
            "url": "https://example.com/products",
            "actions": [
                {"type": "click", "selector": ".product-card:first-child .add-to-cart"},
                {"type": "click", "selector": ".cart-icon"},
                {"type": "click", "selector": ".checkout-button"}
            ]
        },
        "output": {
            "name": "添加商品到购物车并结账",
            "description": "验证用户能够将商品添加到购物车并进入结账流程",
            "steps": [
                {"name": "点击第一个商品的添加到购物车按钮", "action": "click", "selector": ".product-card:first-child .add-to-cart"},
                {"name": "点击购物车图标", "action": "click", "selector": ".cart-icon"},
                {"name": "点击结账按钮", "action": "click", "selector": ".checkout-button"}
            ],
            "assertions": [
                {"type": "elementVisible", "value": ".cart-count", "description": "验证购物车数量显示"},
                {"type": "urlContains", "value": "/checkout", "description": "验证跳转到结账页面"}
            ],
            "variables": {}
        }
    },
    {
        "input": {
            "url": "https://example.com/search",
            "actions": [
                {"type": "type", "selector": "#search-input", "value": "iPhone 15"},
                {"type": "click", "selector": ".search-button"},
                {"type": "click", "selector": ".search-result:first-child"}
            ]
        },
        "output": {
            "name": "搜索商品并查看详情",
            "description": "验证用户能够通过搜索功能找到商品并查看商品详情",
            "steps": [
                {"name": "在搜索框输入关键词", "action": "type", "selector": "#search-input", "value": "${{searchKeyword}}"},
                {"name": "点击搜索按钮", "action": "click", "selector": ".search-button"},
                {"name": "点击第一个搜索结果", "action": "click", "selector": ".search-result:first-child"}
            ],
            "assertions": [
                {"type": "elementVisible", "value": ".search-results", "description": "验证搜索结果显示"},
                {"type": "urlContains", "value": "/product/", "description": "验证跳转到商品详情页"}
            ],
            "variables": {
                "searchKeyword": "iPhone 15"
            }
        }
    }
]

# 生成测试用例
@app.post("/api/ai/generate-case")
async def generate_test_case(request: GenerateCaseRequest):
    # 构建Few-shot示例部分
    examples_text = ""
    for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        examples_text += f"""
示例 {i}:

输入:
URL: {example['input']['url']}
操作序列:
{json.dumps(example['input']['actions'], ensure_ascii=False, indent=2)}

输出:
{json.dumps(example['output'], ensure_ascii=False, indent=2)}

---
"""
    
    # 构建Prompt
    prompt = f"""
你是一个专业的自动化测试专家。请根据以下录制的网页操作，生成一个结构化的测试用例。

{examples_text}

现在，请分析以下录制的操作，并生成测试用例：

目标网页URL: {request.url}

录制的操作序列:
{json.dumps(request.actions, ensure_ascii=False, indent=2)}

请参考上述示例的格式和风格，生成一个测试用例，包含以下内容：
1. name: 测试用例的名称（简洁明了，描述测试目标，使用"动词+名词"格式，如"用户登录测试"、"添加商品到购物车"）
2. description: 测试用例的详细描述（说明测试的目的和预期结果）
3. steps: 优化后的测试步骤，每个步骤包含：
   - name: 步骤名称（人类可读，描述具体操作）
   - action: 操作类型（navigate, click, type, select, check, uncheck, wait, waitForSelector等）
   - selector: 元素选择器（优先使用data-testid、id、name等稳定选择器）
   - value: 输入值（如果有）
4. assertions: 关键步骤后的断言，每个断言包含：
   - type: 断言类型（urlContains, textVisible, elementExists, elementVisible等）
   - value: 断言的期望值
   - description: 断言的描述
5. variables: 识别出的可参数化变量（如用户名、密码、搜索关键词等）

重要规则：
- 将硬编码的值（如用户名、密码、搜索关键词）转换为变量，格式为 ${{variable_name}}
- 在variables中定义变量的默认值
- 为关键步骤添加合理的断言（如登录后验证URL、提交后验证成功消息等）
- 步骤名称应该清晰描述操作意图
- 选择器应该优先使用稳定的属性（data-testid > id > name > class）

返回JSON格式，不要包含任何其他文本。
"""
    
    try:
        # 调用LLM
        response = await LLMGateway.generate(prompt, request.model, request.provider)
        
        # 解析JSON
        generated_case = json.loads(response)
        
        return generated_case
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating test case: {str(e)}")

# 分析业务说明
@app.post("/api/ai/analyze-business")
async def analyze_business_description(request: AnalyzeBusinessRequest):
    try:
        analyzer = BusinessAnalyzer(model=request.model, provider=request.provider)
        result = await analyzer.analyze(request.url, request.description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing business description: {str(e)}")

# 分析测试错误
@app.post("/api/ai/analyze-error")
async def analyze_error(request: AnalyzeErrorRequest):
    # 构建Prompt
    context_parts = [
        f"测试步骤: {request.step_name}",
        f"目标元素选择器: {request.selector}",
        f"错误信息: {request.error_message}"
    ]
    
    if request.screenshot_context:
        context_parts.append(f"截图上下文: {request.screenshot_context}")
    
    if request.dom_context:
        context_parts.append(f"DOM上下文: {request.dom_context[:1000]}...")  # 限制长度
    
    if request.console_logs:
        context_parts.append(f"控制台日志: {json.dumps(request.console_logs[:10], ensure_ascii=False)}")
    
    prompt = f"""
你是一个资深的自动化测试专家。请分析以下测试失败的情况，并提供诊断和修复建议。

{chr(10).join(context_parts)}

请提供以下分析：
1. root_cause: 失败的根本原因（简洁明了）
2. explanations: 可能的解释（列表，每项是一个可能的原因）
3. suggestions: 修复建议（列表，每项是一个具体的修复方案）
4. confidence: 分析的置信度（high, medium, low）

返回JSON格式，不要包含任何其他文本。
"""
    
    try:
        # 调用LLM
        response = await LLMGateway.generate(prompt, request.model, request.provider)
        
        # 解析JSON
        analysis = json.loads(response)
        
        return analysis
    
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing error: {str(e)}")

# 测试LLM连接
@app.get("/api/ai/test-connection")
async def test_connection(provider: str = "zai", model: str = "glm-4.5-air"):
    try:
        response = await LLMGateway.generate(
            "请回复'连接成功'，返回JSON格式: {\"message\": \"连接成功\"}",
            model,
            provider
        )
        result = json.loads(response)
        return {"status": "ok", "provider": provider, "model": model, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
