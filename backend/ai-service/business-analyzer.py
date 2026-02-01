"""
业务说明分析服务
用于解析自然语言业务说明，提取关键功能点和测试目标
"""

from typing import Dict, List, Any
from openai import OpenAI
import os


class BusinessAnalyzer:
    """业务说明分析器"""

    def __init__(self, model: str = "gpt-4.1-mini", provider: str = "openai"):
        self.model = model
        self.provider = provider
        self.openai_client = OpenAI() if provider == "openai" else None

        # Few-shot示例
        self.few_shot_examples = [
            {
                "input": {
                    "url": "https://example.com",
                    "description": "I want to test a login page with the following features:\n- Users can login with username and password\n- There is a forgot password link\n- After login, users see their dashboard"
                },
                "output": {
                    "key_features": [
                        "User authentication via username/password",
                        "Password recovery functionality",
                        "Post-login dashboard navigation"
                    ],
                    "test_targets": [
                        "Login form submission",
                        "Forgot password flow",
                        "Dashboard content verification",
                        "Session state management"
                    ],
                    "priority_areas": [
                        "Authentication flow (high priority)",
                        "Password reset flow (medium priority)",
                        "Dashboard user data display (high priority)"
                    ],
                    "exploration_strategy": "Focus on authentication pages first, then explore authenticated areas",
                    "confidence": "high"
                }
            },
            {
                "input": {
                    "url": "https://shop.example.com",
                    "description": "Test the e-commerce checkout process:\n- Browse products\n- Add items to cart\n- Go to checkout\n- Enter shipping and payment details\n- Complete order"
                },
                "output": {
                    "key_features": [
                        "Product browsing and selection",
                        "Shopping cart management",
                        "Checkout process",
                        "Payment processing"
                    ],
                    "test_targets": [
                        "Product listing and filtering",
                        "Add to cart functionality",
                        "Cart modification (quantity, removal)",
                        "Checkout form validation",
                        "Order confirmation"
                    ],
                    "priority_areas": [
                        "Add to cart flow (critical)",
                        "Checkout process (critical)",
                        "Payment integration (critical)",
                        "Product search (high priority)"
                    ],
                    "exploration_strategy": "Start from homepage, navigate through product pages, add items to cart, complete checkout flow",
                    "confidence": "high"
                }
            },
            {
                "input": {
                    "url": "https://taskapp.example.com",
                    "description": "Test a task management application:\n- Create new tasks\n- Mark tasks as complete\n- Delete tasks\n- Filter tasks by status"
                },
                "output": {
                    "key_features": [
                        "Task creation",
                        "Task status management",
                        "Task deletion",
                        "Task filtering"
                    ],
                    "test_targets": [
                        "New task creation form",
                        "Task completion toggle",
                        "Task delete action",
                        "Filter functionality (all/active/completed)",
                        "Task persistence"
                    ],
                    "priority_areas": [
                        "Task CRUD operations (critical)",
                        "Filter and search (medium priority)",
                        "Task persistence verification (high priority)"
                    ],
                    "exploration_strategy": "Test all CRUD operations on tasks, verify filtering and search features",
                    "confidence": "medium"
                }
            }
        ]

    def build_prompt(self, url: str, description: str) -> str:
        """构建分析提示词"""
        examples_text = ""
        for i, example in enumerate(self.few_shot_examples, 1):
            examples_text += f"""
示例 {i}:

输入:
URL: {example['input']['url']}
业务说明:
{example['input']['description']}

输出:
{self._format_output(example['output'])}

---
"""

        prompt = f"""
你是一个专业的自动化测试专家，擅长分析自然语言业务说明并提取关键测试信息。

{examples_text}

现在，请分析以下业务说明：

目标网页URL: {url}

业务说明:
{description}

请参考上述示例的格式和风格，分析业务说明并提取以下信息：
1. key_features: 识别的关键功能点列表（描述系统的主要功能模块）
2. test_targets: 测试目标列表（需要测试的具体功能点）
3. priority_areas: 优先级区域列表（标注每个区域的优先级：critical/high/medium/low）
4. exploration_strategy: 探索策略描述（建议如何进行网站探索）
5. confidence: 分析的置信度（high/medium/low）

返回JSON格式，不要包含任何其他文本。

注意：
- key_features 应该是高层级的功能模块
- test_targets 应该是具体的可测试功能点
- priority_areas 应该标注每个测试区域的重要性
- exploration_strategy 应该提供清晰的探索路径建议
- confidence 表示对分析结果的确定性程度
"""

        return prompt

    def _format_output(self, output: Dict[str, Any]) -> str:
        """格式化输出为可读字符串"""
        return str(output).replace("'", '"')

    async def analyze(self, url: str, description: str) -> Dict[str, Any]:
        """分析业务说明"""
        try:
            if self.provider == "openai":
                return await self._analyze_with_openai(url, description)
            else:
                # Placeholder for other providers (e.g., Ollama)
                return self._analyze_fallback(url, description)
        except Exception as e:
            print(f"Error analyzing business description: {e}")
            return self._analyze_fallback(url, description)

    async def _analyze_with_openai(self, url: str, description: str) -> Dict[str, Any]:
        """使用OpenAI进行分析"""
        prompt = self.build_prompt(url, description)

        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的自动化测试专家，擅长分析网页操作并生成测试用例。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result

    def _analyze_fallback(self, url: str, description: str) -> Dict[str, Any]:
        """回退分析方法（使用规则和启发式）"""
        import re

        # 基于关键词提取功能点
        keywords_mapping = {
            "login": ["User authentication", "Login functionality"],
            "register": ["User registration", "Sign up process"],
            "password": ["Password management", "Password reset"],
            "checkout": ["Checkout process", "Order completion"],
            "cart": ["Shopping cart", "Cart management"],
            "search": ["Search functionality", "Content search"],
            "filter": ["Filtering", "Content filtering"],
            "dashboard": ["Dashboard", "User dashboard"],
            "profile": ["User profile", "Profile management"],
            "settings": ["Settings", "User settings"],
            "create": ["Create functionality", "Content creation"],
            "update": ["Update functionality", "Content editing"],
            "delete": ["Delete functionality", "Content deletion"],
        }

        key_features = []
        test_targets = []

        # 查找匹配的关键词
        desc_lower = description.lower()
        for keyword, features in keywords_mapping.items():
            if keyword in desc_lower:
                key_features.extend(features)
                test_targets.extend([f"Test {f.lower()}" for f in features])

        # 去重
        key_features = list(dict.fromkeys(key_features))
        test_targets = list(dict.fromkeys(test_targets))

        # 如果没有找到任何特征，使用默认值
        if not key_features:
            key_features = ["General functionality testing"]
            test_targets = ["Basic user interaction"]

        # 生成优先级区域
        priority_areas = []
        for feature in key_features[:3]:
            priority_areas.append(f"{feature} (medium priority)")

        # 生成探索策略
        exploration_strategy = "Explore the main page first, then navigate through identified features"

        return {
            "key_features": key_features,
            "test_targets": test_targets,
            "priority_areas": priority_areas,
            "exploration_strategy": exploration_strategy,
            "confidence": "medium"
        }
