"""
用例生成器测试
测试自动用例生成功能
"""

import pytest
from case_generator import TestCaseGenerator, TestCase, TestStep, TestCasePriority
from case_deduplicator import CaseDeduplicator, CaseSignature
from coverage_reporter import CoverageReporter, CoverageMetric, CoverageResult


class TestTestCaseGenerator:
    """测试用例生成器测试"""

    def test_initialization(self):
        """测试生成器初始化"""
        generator = TestCaseGenerator()
        assert generator.generated_cases == []

    def test_detect_form_type_login(self):
        """测试检测登录表单类型"""
        generator = TestCaseGenerator()

        form = {
            "action": "/login",
            "method": "POST",
            "fields": [
                {"type": "text", "name": "username"},
                {"type": "password", "name": "password"}
            ]
        }

        form_type = generator._detect_form_type(form)

        assert form_type == "login"

    def test_detect_form_type_search(self):
        """测试检测搜索表单类型"""
        generator = TestCaseGenerator()

        form = {
            "action": "/search",
            "method": "GET",
            "fields": [
                {"type": "text", "name": "search"}
            ]
        }

        form_type = generator._detect_form_type(form)

        assert form_type == "search"

    def test_detect_form_type_register(self):
        """测试检测注册表单类型"""
        generator = TestCaseGenerator()

        form = {
            "action": "/register",
            "method": "POST",
            "fields": [
                {"type": "email", "name": "email"}
            ]
        }

        form_type = generator._detect_form_type(form)

        assert form_type == "register"

    def test_generate_test_value(self):
        """测试生成测试数据"""
        generator = TestCaseGenerator()

        # 密码字段
        password_value = generator._generate_test_value("password", "pass")
        assert "@" in password_value  # 包含特殊字符

        # 邮箱字段
        email_value = generator._generate_test_value("email", "email")
        assert "@" in email_value
        assert "." in email_value

        # 文本字段
        text_value = generator._generate_test_value("text", "name")
        assert isinstance(text_value, str)

    def test_generate_test_case_for_login(self):
        """测试为登录表单生成测试用例"""
        generator = TestCaseGenerator()

        form = {
            "action": "/login",
            "method": "POST",
            "fields": [
                {"type": "text", "name": "username", "selector": "#username"},
                {"type": "password", "name": "password", "selector": "#password"}
            ],
            "submit_button": "#submit-btn"
        }

        page = {
            "url": "http://example.com/login"
        }

        test_case = generator._generate_form_test_case(form, page)

        assert test_case is not None
        assert "登录" in test_case.name
        assert test_case.priority == TestCasePriority.CRITICAL
        assert len(test_case.steps) > 0
        assert len(test_case.assertions) > 0

    def test_generate_test_case_to_dict(self):
        """测试用例转字典"""
        generator = TestCaseGenerator()

        test_case = TestCase(
            name="测试用例",
            description="测试描述",
            priority=TestCasePriority.HIGH,
            steps=[
                TestStep(name="步骤1", action="navigate", selector="url", value="http://example.com"),
                TestStep(name="步骤2", action="click", selector="button")
            ],
            assertions=[
                {"type": "urlContains", "value": "/home", "description": "验证跳转"}
            ],
            tags=["smoke", "e2e"],
            estimated_duration=10
        )

        case_dict = test_case.to_dict()

        assert case_dict["name"] == "测试用例"
        assert case_dict["priority"] == "high"
        assert len(case_dict["steps"]) == 2
        assert len(case_dict["assertions"]) == 1

    def test_generate_cases_from_exploration(self):
        """测试从探索结果生成测试用例"""
        generator = TestCaseGenerator()

        exploration_results = {
            "pages": [
                {
                    "url": "http://example.com",
                    "forms_found": [
                        {
                            "action": "/login",
                            "method": "POST",
                            "fields": [
                                {"type": "text", "name": "username", "selector": "#username"},
                                {"type": "password", "name": "password", "selector": "#password"}
                            ],
                            "submit_button": "#submit"
                        }
                    ],
                    "links_found": ["http://example.com/page1", "http://example.com/page2"],
                    "interactive_elements": []
                }
            ],
            "discovered_cases": []
        }

        cases = generator.generate_cases_from_exploration(exploration_results)

        # 应该生成登录测试用例
        login_cases = [c for c in cases if "登录" in c.name]
        assert len(login_cases) > 0

    def test_deduplicate_cases(self):
        """测试用例去重"""
        generator = TestCaseGenerator()

        # 添加重复的用例
        generator.generated_cases = [
            TestCase(
                name="登录测试",
                description="测试登录",
                priority=TestCasePriority.CRITICAL,
                steps=[],
                assertions=[],
                tags=["login"],
                estimated_duration=5
            ),
            TestCase(
                name="登录测试",
                description="测试登录",
                priority=TestCasePriority.CRITICAL,
                steps=[],
                assertions=[],
                tags=["login"],
                estimated_duration=5
            )
        ]

        unique_cases = generator._deduplicate_cases()

        # 去重后应该只有一个用例
        assert len(unique_cases) == 1

    def test_prioritize_cases(self):
        """测试用例优先级排序"""
        generator = TestCaseGenerator()

        generator.generated_cases = [
            TestCase(
                name="低优先级测试",
                description="低",
                priority=TestCasePriority.LOW,
                steps=[],
                assertions=[],
                tags=["test"],
                estimated_duration=1
            ),
            TestCase(
                name="高优先级测试",
                description="高",
                priority=TestCasePriority.HIGH,
                steps=[],
                assertions=[],
                tags=["test"],
                estimated_duration=1
            ),
            TestCase(
                name="关键测试",
                description="关键",
                priority=TestCasePriority.CRITICAL,
                steps=[],
                assertions=[],
                tags=["test"],
                estimated_duration=1
            )
        ]

        prioritized = generator.prioritize_cases()

        # 应该按优先级排序
        assert prioritized[0].priority == TestCasePriority.CRITICAL
        assert prioritized[1].priority == TestCasePriority.HIGH
        assert prioritized[2].priority == TestCasePriority.LOW

    def test_get_case_summary(self):
        """测试获取用例摘要"""
        generator = TestCaseGenerator()

        generator.generated_cases = [
            TestCase(
                name="登录测试",
                description="测试登录",
                priority=TestCasePriority.CRITICAL,
                steps=[],
                assertions=[],
                tags=["login", "form", "e2e"],
                estimated_duration=5
            ),
            TestCase(
                name="搜索测试",
                description="测试搜索",
                priority=TestCasePriority.HIGH,
                steps=[],
                assertions=[],
                tags=["search"],
                estimated_duration=3
            )
        ]

        summary = generator.get_case_summary()

        assert summary["total"] == 2
        assert summary["by_priority"]["critical"] == 1
        assert summary["by_priority"]["high"] == 1
        assert "login" in summary["by_tag"]


class TestCaseDeduplicator:
    """用例去重器测试"""

    def test_initialization(self):
        """测试去重器初始化"""
        deduplicator = CaseDeduplicator()
        assert deduplicator.similarity_threshold == 0.7

    def test_generate_case_signature(self):
        """测试生成用例签名"""
        deduplicator = CaseDeduplicator()

        case = {
            "name": "登录测试",
            "steps": [
                {"selector": "#username"},
                {"selector": "#password"}
            ]
        }

        signature = deduplicator._generate_signature(case)

        assert isinstance(signature, CaseSignature)
        assert signature.name_hash is not None
        assert signature.steps_hash is not None

    def test_calculate_similarity(self):
        """测试计算字符串相似度"""
        deduplicator = CaseDeduplicator()

        # 完全相同
        assert deduplicator._calculate_similarity("test", "test") == 1.0

        # 完全不同
        assert deduplicator._calculate_similarity("abc", "xyz") < 1.0

        # 部分相同
        similarity = deduplicator._calculate_similarity("test", "testing")
        assert 0 < similarity < 1.0

    def test_are_similar_cases(self):
        """测试判断用例是否相似"""
        deduplicator = CaseDeduplicator()

        case1 = {
            "name": "登录测试",
            "steps": [
                {"selector": "#username"},
                {"selector": "#password"}
            ],
            "tags": ["login"]
        }

        case2 = {
            "name": "登录测试",
            "steps": [
                {"selector": "#username"},
                {"selector": "#password"}
            ],
            "tags": ["login"]
        }

        assert deduplicator._are_similar(case1, case2)

    def test_deduplicate_cases(self):
        """测试用例去重"""
        deduplicator = CaseDeduplicator()

        cases = [
            {
                "name": "登录测试",
                "steps": [{"selector": "#username"}],
                "tags": ["login"]
            },
            {
                "name": "登录测试",
                "steps": [{"selector": "#username"}],
                "tags": ["login"]
            },
            {
                "name": "搜索测试",
                "steps": [{"selector": "#search"}],
                "tags": ["search"]
            }
        ]

        unique = deduplicator.deduplicate_cases(cases)

        # 应该去重一个登录测试
        assert len(unique) == 2

    def test_select_best_case(self):
        """测试选择最佳用例"""
        deduplicator = CaseDeduplicator()

        cases = [
            {
                "name": "低优先级",
                "steps": [],
                "priority": "low",
                "assertions": []
            },
            {
                "name": "高优先级",
                "steps": [],
                "priority": "high",
                "assertions": []
            }
        ]

        best = deduplicator._select_best_case(cases)

        # 应该选择高优先级的用例
        assert best["priority"] == "high"


class TestCoverageReporter:
    """覆盖度报告测试"""

    def test_initialization(self):
        """测试报告器初始化"""
        reporter = CoverageReporter()
        assert reporter.results == []

    def test_calculate_page_coverage(self):
        """测试计算页面覆盖度"""
        reporter = CoverageReporter()

        exploration_results = {
            "pages": [
                {"url": "http://example.com/page1"},
                {"url": "http://example.com/page2"},
                {"url": "http://example.com/page3"}
            ]
        }

        test_cases = [
            {
                "steps": [
                    {"action": "navigate", "value": "http://example.com/page1"},
                    {"action": "click", "selector": "button"}
                ]
            }
        ]

        result = reporter._calculate_page_coverage(
            exploration_results["pages"],
            test_cases
        )

        assert isinstance(result, CoverageResult)
        assert result.metric == CoverageMetric.PAGE_COVERAGE
        assert result.total == 3

    def test_calculate_element_coverage(self):
        """测试计算元素覆盖度"""
        reporter = CoverageReporter()

        exploration_results = {
            "pages": [
                {
                    "interactive_elements": [
                        {"selector": "#button1"},
                        {"selector": "#button2"},
                        {"selector": "#input1"}
                    ]
                }
            ]
        }

        test_cases = [
            {
                "steps": [
                    {"selector": "#button1"},
                    {"selector": "#input1"}
                ]
            }
        ]

        result = reporter._calculate_element_coverage(
            exploration_results["pages"],
            test_cases
        )

        assert isinstance(result, CoverageResult)
        assert result.metric == CoverageMetric.ELEMENT_COVERAGE
        assert result.total == 3

    def test_calculate_coverage(self):
        """测试计算整体覆盖度"""
        reporter = CoverageReporter()

        exploration_results = {
            "pages": [
                {"url": "http://example.com/page1"},
                {"interactive_elements": [{"selector": "#btn1"}]}
            ]
        }

        test_cases = [
            {
                "steps": [{"action": "navigate", "value": "http://example.com/page1"}],
                "tags": ["form"]
            }
        ]

        report = reporter.calculate_coverage(exploration_results, test_cases)

        assert "summary" in report
        assert "metrics" in report
        assert len(report["metrics"]) > 0

    def test_generate_report(self):
        """测试生成覆盖度报告"""
        reporter = CoverageReporter()

        exploration_results = {
            "pages": [
                {"url": "http://example.com/page1", "interactive_elements": []}
            ]
        }

        test_cases = [{"steps": [], "tags": ["form"]}]

        report = reporter.calculate_coverage(exploration_results, test_cases)
        generated = reporter._generate_report()

        assert "summary" in generated
        assert "metrics" in generated
        assert "recommendations" in generated

    def test_export_to_json(self):
        """测试导出JSON"""
        reporter = CoverageReporter()

        exploration_results = {
            "pages": [
                {"url": "http://example.com/page1", "interactive_elements": []}
            ]
        }

        test_cases = [{"steps": [], "tags": ["form"]}]

        report = reporter.calculate_coverage(exploration_results, test_cases)

        json_str = reporter.export_report(format="json")

        assert json_str is not None
        assert isinstance(json_str, str)

    def test_export_to_markdown(self):
        """测试导出Markdown"""
        reporter = CoverageReporter()

        exploration_results = {
            "pages": [
                {"url": "http://example.com/page1", "interactive_elements": []}
            ]
        }

        test_cases = [{"steps": [], "tags": ["form"]}]

        report = reporter.calculate_coverage(exploration_results, test_cases)

        md_str = reporter.export_report(format="markdown")

        assert md_str is not None
        assert isinstance(md_str, str)
        assert "# 测试覆盖度报告" in md_str


# 运行测试的入口
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
