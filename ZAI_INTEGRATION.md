# Z.AI GLM-4.5-AIR 集成配置

## 概述

AI赋能的网页自动化测试工具现已支持z.ai的glm-4.5-air模型，为用户提供更多的AI模型选择。

## 配置步骤

### 1. 获取Z.AI API密钥

1. 访问 [z.ai官方网站](https://open.bigmodel.cn/)
2. 注册并登录账户
3. 在控制台中获取API密钥

### 2. 设置环境变量

在运行应用之前，设置以下环境变量：

```bash
# Linux/Mac
export ZAI_API_KEY="your_zai_api_key_here"
export ZAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"

# Windows (PowerShell)
$env:ZAI_API_KEY="your_zai_api_key_here"
$env:ZAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4/"
```

### 3. 可选配置

您也可以同时保留其他AI模型的配置：

```bash
# OpenAI配置
export OPENAI_API_KEY="your_openai_api_key_here"

# Ollama配置
export OLLAMA_BASE_URL="http://localhost:11434"
```

## 使用方法

### 通过前端界面

1. 启动应用后，访问管理界面
2. 在AI服务配置部分，选择"zai"作为提供商
3. 选择"glm-4.5-air"作为模型
4. 保存配置

### 通过API调用

#### 生成测试用例

```python
import requests

response = requests.post('http://localhost:8003/api/ai/generate-case', json={
    "url": "https://example.com",
    "actions": [
        {"type": "click", "selector": "#submit"}
    ],
    "model": "glm-4.5-air",
    "provider": "zai"
})
```

#### 分析测试错误

```python
response = requests.post('http://localhost:8003/api/ai/analyze-error', json={
    "error_message": "Element not found",
    "step_name": "点击提交按钮",
    "selector": "#submit",
    "model": "glm-4.5-air",
    "provider": "zai"
})
```

#### 测试连接

```python
response = requests.get('http://localhost:8003/api/ai/test-connection?provider=zai&model=glm-4.5-air')
```

## 支持的模型

| 提供商 | 模型名称 | 描述 |
|--------|----------|------|
| zai | glm-4.5-air | 智谱AI通用大语言模型 |

## 注意事项

1. **API密钥安全**：请妥善保管您的z.ai API密钥，不要在代码中硬编码或提交到版本控制系统
2. **费用**：使用z.ai模型会产生相应的费用，请查看官方定价页面
3. **速率限制**：请注意API的调用频率限制
4. **网络连接**：确保应用可以访问z.ai的API端点

## 故障排除

### 常见错误

1. **ZAI API key not configured**
   - 检查是否设置了ZAI_API_KEY环境变量
   - 确认API密钥是否正确

2. **ZAI API error**
   - 检查网络连接
   - 确认API密钥是否有效
   - 查看z.ai控制台的错误信息

### 调试建议

1. 使用测试连接端点验证配置
2. 查看应用的日志输出
3. 使用curl直接测试API调用

## 性能优化建议

1. 批量处理测试用例生成，减少API调用次数
2. 合理设置temperature参数以平衡创造性和一致性
3. 对于简单的测试场景，可以使用更小的模型以节省成本

## 更新日志

- **2026-02-02**: 首次添加z.ai glm-4.5-air模型支持