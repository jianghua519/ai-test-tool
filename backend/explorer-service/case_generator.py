"""
自动用例生成器
基于探索路径和发现的元素生成测试用例
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class TestCasePriority(Enum):
    """测试用例优先级"""
    CRITICAL = "critical"    # 核心功能，必须测试
    HIGH = "high"          # 重要功能，高优先级
    MEDIUM = "medium"      # 一般功能，中优先级
    LOW = "low"            # 次要功能，低优先级


@dataclass
class TestStep:
    """测试步骤"""
    name: str
    action: str
    selector: str
    value: Optional[str] = None
    wait_after: int = 1000


@dataclass
class TestCase:
    """测试用例"""
    name: str
    description: str
    priority: TestCasePriority
    steps: List[TestStep]
    assertions: List[Dict[str, Any]]
    tags: List[str]
    estimated_duration: int  # 预估执行时间（秒）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "steps": [
                {
                    "name": step.name,
                    "action": step.action,
                    "selector": step.selector,
                    "value": step.value
                }
                for step in self.steps
            ],
            "assertions": self.assertions,
            "tags": self.tags,
            "estimated_duration": self.estimated_duration
        }


class TestCaseGenerator:
    """测试用例生成器"""

    def __init__(self):
        self.generated_cases: List[TestCase] = []

    def generate_cases_from_exploration(
        self,
        exploration_results: Dict[str, Any]
    ) -> List[TestCase]:
        """基于探索结果生成测试用例"""
        self.generated_cases = []

        # 获取探索的页面和元素
        pages = exploration_results.get("pages", [])
        discovered_cases = exploration_results.get("discovered_cases", [])

        # 1. 从发现的表单生成表单测试用例
        for page in pages:
            for form in page.get("forms_found", []):
                test_case = self._generate_form_test_case(form, page)
                if test_case:
                    self.generated_cases.append(test_case)

        # 2. 从导航路径生成导航测试用例
        navigation_cases = self._generate_navigation_test_cases(pages)
        self.generated_cases.extend(navigation_cases)

        # 3. 从交互元素生成交互测试用例
        for page in pages:
            interactive_cases = self._generate_interaction_test_cases(page)
            self.generated_cases.extend(interactive_cases)

        # 4. 生成搜索功能测试用例
        search_cases = self._generate_search_test_cases(pages)
        self.generated_cases.extend(search_cases)

        # 去重
        self.generated_cases = self._deduplicate_cases()

        return self.generated_cases

    def _generate_form_test_case(
        self,
        form: Dict[str, Any],
        page: Dict[str, Any]
    ) -> Optional[TestCase]:
        """生成表单测试用例"""
        fields = form.get("fields", [])
        action = form.get("action", "")

        if not fields:
            return None

        # 判断表单类型
        form_type = self._detect_form_type(form)

        # 生成用例名称和描述
        if form_type == "login":
            name = "用户登录测试"
            description = "测试用户使用用户名和密码登录功能"
            priority = TestCasePriority.CRITICAL
        elif form_type == "register":
            name = "用户注册测试"
            description = "测试用户注册功能"
            priority = TestCasePriority.HIGH
        elif form_type == "search":
            name = "搜索功能测试"
            description = "测试网站搜索功能"
            priority = TestCasePriority.HIGH
        else:
            name = f"表单提交测试 - {action}"
            description = f"测试表单提交功能，表单action: {action}"
            priority = TestCasePriority.MEDIUM

        # 生成测试步骤
        steps = []
        steps.append(TestStep(
            name="导航到表单页面",
            action="navigate",
            selector=page.get("url"),
            value=page.get("url")
        ))

        for field in fields:
            field_name = field.get("name", "")
            field_type = field.get("type", "text")

            # 生成测试数据
            test_value = self._generate_test_value(field_type, field_name)

            steps.append(TestStep(
                name=f"填写{field_name}字段",
                action="type",
                selector=field.get("selector", ""),
                value=test_value
            ))

        # 添加提交步骤
        submit_button = form.get("submit_button")
        if submit_button:
            steps.append(TestStep(
                name="点击提交按钮",
                action="click",
                selector=submit_button
            ))

        # 生成断言
        assertions = self._generate_form_assertions(form_type, action)

        # 估算执行时间
        duration = len(steps) * 2

        return TestCase(
            name=name,
            description=description,
            priority=priority,
            steps=steps,
            assertions=assertions,
            tags=[form_type, "form", "e2e"],
            estimated_duration=duration
        )

    def _generate_navigation_test_cases(
        self,
        pages: List[Dict[str, Any]]
    ) -> List[TestCase]:
        """生成导航测试用例"""
        cases = []

        # 为主要页面生成导航测试
        for page in pages:
            if page.get("depth", 0) <= 1:  # 只生成浅层页面的导航测试
                url = page.get("url", "")
                links = page.get("links_found", [])

                if links:
                    # 选择前3个链接进行测试
                    for i, link in enumerate(links[:3]):
                        steps = [
                            TestStep(
                                name=f"导航到页面 {i+1}",
                                action="navigate",
                                selector=url,
                                value=url
                            ),
                            TestStep(
                                name=f"点击链接: {link}",
                                action="click",
                                selector=f"a[href='{link}']"  # 简化的选择器
                            )
                        ]

                        cases.append(TestCase(
                            name=f"导航测试 - 页面{i+1}",
                            description=f"测试从 {url} 导航到 {link}",
                            priority=TestCasePriority.MEDIUM,
                            steps=steps,
                            assertions=[{
                                "type": "urlContains",
                                "value": link,
                                "description": "验证跳转到目标页面"
                            }],
                            tags=["navigation", "smoke"],
                            estimated_duration=5
                        ))

        return cases

    def _generate_interaction_test_cases(
        self,
        page: Dict[str, Any]
    ) -> List[TestCase]:
        """生成交互测试用例"""
        cases = []

        interactive_elements = page.get("interactive_elements", [])

        # 为重要的交互元素生成测试
        for i, element in enumerate(interactive_elements[:5]):
            element_type = element.get("type", "unknown")
            selector = element.get("selector", "")
            text = element.get("text", "")[:50]

            if element_type in ["button", "link"]:
                steps = [
                    TestStep(
                        name="导航到页面",
                        action="navigate",
                        selector=page.get("url"),
                        value=page.get("url")
                    ),
                    TestStep(
                        name=f"点击{text or element_type}",
                        action="click",
                        selector=selector
                    )
                ]

                cases.append(TestCase(
                    name=f"交互测试 - 点击{text or element_type} {i+1}",
                    description=f"测试点击{element_type}元素",
                    priority=TestCasePriority.LOW,
                    steps=steps,
                    assertions=[{
                        "type": "elementExists",
                        "value": selector,
                        "description": "验证元素存在且可点击"
                    }],
                    tags=["interaction", "ui"],
                    estimated_duration=3
                ))

        return cases

    def _generate_search_test_cases(
        self,
        pages: List[Dict[str, Any]]
    ) -> List[TestCase]:
        """生成搜索功能测试用例"""
        cases = []

        for page in pages:
            forms = page.get("forms_found", [])

            for form in forms:
                if self._detect_form_type(form) == "search":
                    steps = [
                        TestStep(
                            name="导航到搜索页面",
                            action="navigate",
                            selector=page.get("url"),
                            value=page.get("url")
                        ),
                        TestStep(
                            name="输入搜索关键词",
                            action="type",
                            selector=form.get("fields", [{}])[0].get("selector", ""),
                            value="test"
                        ),
                        TestStep(
                            name="点击搜索按钮",
                            action="click",
                            selector=form.get("submit_button", "")
                        )
                    ]

                    cases.append(TestCase(
                        name="搜索功能测试",
                        description="测试网站的搜索功能",
                        priority=TestCasePriority.HIGH,
                        steps=steps,
                        assertions=[
                            {
                                "type": "elementVisible",
                                "value": ".search-results",
                                "description": "验证搜索结果显示"
                            }
                        ],
                        tags=["search", "e2e"],
                        estimated_duration=5
                    ))

        return cases

    def _detect_form_type(self, form: Dict[str, Any]) -> str:
        """检测表单类型"""
        action = form.get("action", "").lower()
        fields = form.get("fields", [])

        # 检查是否有密码字段
        for field in fields:
            if field.get("type") == "password" or "password" in field.get("name", "").lower():
                return "login"

        # 检查是否有邮箱字段（但没有密码）
        has_email = any("email" in field.get("name", "").lower() for field in fields)
        if has_email:
            return "register"

        # 检查搜索关键字
        if "search" in action or any("search" in field.get("name", "").lower() for field in fields):
            return "search"

        return "general"

    def _generate_test_value(self, field_type: str, field_name: str) -> str:
        """生成测试数据"""
        test_values = {
            "password": "Test@123",
            "email": "test@example.com",
            "text": "test",
            "number": "123",
            "date": "2024-01-01",
            "tel": "1234567890"
        }

        return test_values.get(field_type, "test")

    def _generate_form_assertions(self, form_type: str, action: str) -> List[Dict[str, Any]]:
        """生成表单断言"""
        assertions = []

        if form_type == "login":
            assertions.append({
                "type": "urlContains",
                "value": "/dashboard" or "/home",
                "description": "验证登录后跳转到主页"
            })
        elif form_type == "search":
            assertions.append({
                "type": "elementVisible",
                "value": ".search-results",
                "description": "验证搜索结果显示"
            })
        else:
            assertions.append({
                "type": "urlContains",
                "value": action,
                "description": "验证表单提交成功"
            })

        return assertions

    def _deduplicate_cases(self) -> List[TestCase]:
        """去重测试用例"""
        unique_cases = []
        seen_signatures: Set[str] = []

        for case in self.generated_cases:
            # 生成用例签名（基于名称和步骤数量）
            signature = f"{case.name}_{len(case.steps)}"

            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_cases.append(case)

        return unique_cases

    def prioritize_cases(self) -> List[TestCase]:
        """对测试用例进行优先级排序"""
        priority_order = {
            TestCasePriority.CRITICAL: 0,
            TestCasePriority.HIGH: 1,
            TestCasePriority.MEDIUM: 2,
            TestCasePriority.LOW: 3
        }

        sorted_cases = sorted(
            self.generated_cases,
            key=lambda x: priority_order.get(x.priority, 4)
        )

        return sorted_cases

    def get_case_summary(self) -> Dict[str, Any]:
        """获取测试用例摘要"""
        if not self.generated_cases:
            return {
                "total": 0,
                "by_priority": {},
                "by_tag": {}
            }

        total = len(self.generated_cases)

        # 按优先级统计
        by_priority = {}
        for case in self.generated_cases:
            priority = case.priority.value
            by_priority[priority] = by_priority.get(priority, 0) + 1

        # 按标签统计
        by_tag = {}
        for case in self.generated_cases:
            for tag in case.tags:
                by_tag[tag] = by_tag.get(tag, 0) + 1

        return {
            "total": total,
            "by_priority": by_priority,
            "by_tag": by_tag
        }

    def export_cases_to_json(self) -> str:
        """导出测试用例为JSON"""
        return json.dumps(
            [case.to_dict() for case in self.generated_cases],
            indent=2,
            ensure_ascii=False
        )
