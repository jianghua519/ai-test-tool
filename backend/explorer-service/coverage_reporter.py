"""
覆盖报告生成器
生成测试覆盖度报告
"""

from typing import Dict, List, Any, Set
from dataclasses import dataclass
from enum import Enum
import json


class CoverageMetric(Enum):
    """覆盖度指标"""
    PAGE_COVERAGE = "page_coverage"  # 页面覆盖度
    ELEMENT_COVERAGE = "element_coverage"  # 元素覆盖度
    LINK_COVERAGE = "link_coverage"  # 链接覆盖度
    FORM_COVERAGE = "form_coverage"  # 表单覆盖度
    FEATURE_COVERAGE = "feature_coverage"  # 功能覆盖度


@dataclass
class CoverageResult:
    """覆盖度结果"""
    metric: CoverageMetric
    covered: int
    total: int
    percentage: float
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric.value,
            "covered": self.covered,
            "total": self.total,
            "percentage": round(self.percentage, 2),
            "details": self.details
        }


class CoverageReporter:
    """覆盖度报告生成器"""

    def __init__(self):
        self.results: List[CoverageResult] = []

    def calculate_coverage(
        self,
        exploration_results: Dict[str, Any],
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算整体覆盖度"""
        self.results = []

        # 获取探索数据
        pages = exploration_results.get("pages", [])
        explored_urls = set(p.get("url") for p in pages)

        # 1. 页面覆盖度
        page_coverage = self._calculate_page_coverage(pages, test_cases)
        self.results.append(page_coverage)

        # 2. 元素覆盖度
        element_coverage = self._calculate_element_coverage(pages, test_cases)
        self.results.append(element_coverage)

        # 3. 链接覆盖度
        link_coverage = self._calculate_link_coverage(pages, test_cases)
        self.results.append(link_coverage)

        # 4. 表单覆盖度
        form_coverage = self._calculate_form_coverage(pages, test_cases)
        self.results.append(form_coverage)

        # 5. 功能覆盖度
        feature_coverage = self._calculate_feature_coverage(test_cases)
        self.results.append(feature_coverage)

        # 生成报告
        report = self._generate_report()

        return report

    def _calculate_page_coverage(
        self,
        pages: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]]
    ) -> CoverageResult:
        """计算页面覆盖度"""
        total_pages = len(pages)
        covered_pages = set()

        # 从测试用例中提取被测试的页面
        for case in test_cases:
            steps = case.get("steps", [])
            for step in steps:
                # 如果步骤有value且是URL
                value = step.get("value", "")
                if value and (value.startswith("http") or value.startswith("/")):
                    covered_pages.add(value)

        coverage = len(covered_pages) / total_pages if total_pages > 0 else 0

        return CoverageResult(
            metric=CoverageMetric.PAGE_COVERAGE,
            covered=len(covered_pages),
            total=total_pages,
            percentage=coverage * 100,
            details={
                "covered_pages": list(covered_pages),
                "uncovered_pages": [p.get("url") for p in pages if p.get("url") not in covered_pages]
            }
        )

    def _calculate_element_coverage(
        self,
        pages: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]]
    ) -> CoverageResult:
        """计算元素覆盖度"""
        total_elements = 0
        covered_selectors = set()

        # 统计总元素数
        for page in pages:
            interactive_elements = page.get("interactive_elements", [])
            total_elements += len(interactive_elements)

        # 从测试用例中提取被测试的元素
        for case in test_cases:
            steps = case.get("steps", [])
            for step in steps:
                selector = step.get("selector", "")
                if selector:
                    covered_selectors.add(selector)

        # 从断言中提取被验证的元素
        for case in test_cases:
            assertions = case.get("assertions", [])
            for assertion in assertions:
                value = assertion.get("value", "")
                if value and (value.startswith(".") or value.startswith("#") or value.startswith("[")):
                    covered_selectors.add(value)

        coverage = len(covered_selectors) / total_elements if total_elements > 0 else 0

        return CoverageResult(
            metric=CoverageMetric.ELEMENT_COVERAGE,
            covered=len(covered_selectors),
            total=total_elements,
            percentage=coverage * 100,
            details={
                "covered_selectors": list(covered_selectors),
                "total_interactive_elements": total_elements
            }
        )

    def _calculate_link_coverage(
        self,
        pages: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]]
    ) -> CoverageResult:
        """计算链接覆盖度"""
        total_links = 0
        covered_links = set()

        # 统计总链接数
        for page in pages:
            links = page.get("links_found", [])
            total_links += len(links)

        # 从测试用例中提取被测试的链接
        for case in test_cases:
            steps = case.get("steps", [])
            for step in steps:
                # 点击链接操作
                if step.get("action") == "click":
                    selector = step.get("selector", "")
                    # 简化：假设包含href的选择器是链接
                    if "href=" in selector or selector.startswith("a"):
                        covered_links.add(selector)

        coverage = len(covered_links) / total_links if total_links > 0 else 0

        return CoverageResult(
            metric=CoverageMetric.LINK_COVERAGE,
            covered=len(covered_links),
            total=total_links,
            percentage=coverage * 100,
            details={
                "tested_links": list(covered_links),
                "total_discovered_links": total_links
            }
        )

    def _calculate_form_coverage(
        self,
        pages: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]]
    ) -> CoverageResult:
        """计算表单覆盖度"""
        total_forms = 0
        covered_forms = set()

        # 统计总表单数
        for page in pages:
            forms = page.get("forms_found", [])
            total_forms += len(forms)

        # 从测试用例中提取被测试的表单
        for case in test_cases:
            tags = case.get("tags", [])
            if "form" in tags:
                covered_forms.add(case.get("name", ""))

        coverage = len(covered_forms) / total_forms if total_forms > 0 else 0

        return CoverageResult(
            metric=CoverageMetric.FORM_COVERAGE,
            covered=len(covered_forms),
            total=total_forms,
            percentage=coverage * 100,
            details={
                "tested_forms": list(covered_forms),
                "total_discovered_forms": total_forms
            }
        )

    def _calculate_feature_coverage(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> CoverageResult:
        """计算功能覆盖度"""
        # 预定义的功能类型
        expected_features = {
            "login": "用户登录",
            "register": "用户注册",
            "search": "搜索功能",
            "navigation": "页面导航",
            "form": "表单提交",
            "interaction": "用户交互",
            "e2e": "端到端流程"
        }

        covered_features = set()

        # 从测试用例的标签中提取覆盖的功能
        for case in test_cases:
            tags = case.get("tags", [])
            for tag in tags:
                if tag in expected_features:
                    covered_features.add(tag)

        coverage = len(covered_features) / len(expected_features)

        return CoverageResult(
            metric=CoverageMetric.FEATURE_COVERAGE,
            covered=len(covered_features),
            total=len(expected_features),
            percentage=coverage * 100,
            details={
                "covered_features": [expected_features.get(f, f) for f in covered_features],
                "uncovered_features": [
                    expected_features.get(f, f)
                    for f in expected_features.keys()
                    if f not in covered_features
                ]
            }
        )

    def _generate_report(self) -> Dict[str, Any]:
        """生成覆盖度报告"""
        # 计算平均覆盖度
        if self.results:
            avg_coverage = sum(r.percentage for r in self.results) / len(self.results)
        else:
            avg_coverage = 0

        # 生成建议
        recommendations = self._generate_recommendations()

        return {
            "summary": {
                "average_coverage": round(avg_coverage, 2),
                "total_metrics": len(self.results),
                "timestamp": self._get_timestamp()
            },
            "metrics": [r.to_dict() for r in self.results],
            "recommendations": recommendations,
            "status": self._get_coverage_status(avg_coverage)
        }

    def _generate_recommendations(self) -> List[str]:
        """生成覆盖度改进建议"""
        recommendations = []

        for result in self.results:
            if result.percentage < 50:
                metric = result.metric.value
                recommendations.append(
                    f"{metric} 覆盖度较低 ({result.percentage:.1f}%)，"
                    f"建议增加{metric}相关的测试用例"
                )
            elif result.percentage < 80:
                metric = result.metric.value
                recommendations.append(
                    f"{metric} 覆盖度有待提高 ({result.percentage:.1f}%)，"
                    f"可以考虑添加更多{metric}测试"
                )

        if not recommendations:
            recommendations.append("覆盖度良好，建议持续监控和维护测试用例")

        return recommendations

    def _get_coverage_status(self, coverage: float) -> str:
        """获取覆盖度状态"""
        if coverage >= 80:
            return "excellent"
        elif coverage >= 60:
            return "good"
        elif coverage >= 40:
            return "moderate"
        else:
            return "poor"

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def export_report(self, format: str = "json") -> str:
        """导出报告"""
        report = self._generate_report()

        if format == "json":
            return json.dumps(report, indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._export_to_markdown(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_to_markdown(self, report: Dict[str, Any]) -> str:
        """导出为Markdown格式"""
        lines = []

        lines.append("# 测试覆盖度报告")
        lines.append("")
        lines.append(f"**生成时间**: {report['summary']['timestamp']}")
        lines.append("")

        # 摘要
        lines.append("## 摘要")
        lines.append("")
        lines.append(f"- **平均覆盖度**: {report['summary']['average_coverage']}%")
        lines.append(f"- **状态**: {report['status']}")
        lines.append("")

        # 各项指标
        lines.append("## 覆盖度指标")
        lines.append("")

        for metric in report["metrics"]:
            lines.append(f"### {metric['metric']}")
            lines.append("")
            lines.append(f"- **覆盖**: {metric['covered']} / {metric['total']}")
            lines.append(f"- **百分比**: {metric['percentage']}%")
            lines.append("")

        # 建议
        lines.append("## 改进建议")
        lines.append("")

        for i, rec in enumerate(report["recommendations"], 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)


class TestCaseSummary:
    """测试用例摘要"""

    @staticmethod
    def generate_summary(
        exploration_results: Dict[str, Any],
        test_cases: List[Dict[str, Any]],
        coverage_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成测试用例摘要"""
        # 基础统计
        total_cases = len(test_cases)
        total_pages = len(exploration_results.get("pages", []))
        total_elements = sum(
            len(p.get("interactive_elements", []))
            for p in exploration_results.get("pages", [])
        )

        # 按优先级统计
        priority_count = {}
        for case in test_cases:
            priority = case.get("priority", "unknown")
            priority_count[priority] = priority_count.get(priority, 0) + 1

        # 按类型统计
        type_count = {}
        for case in test_cases:
            for tag in case.get("tags", []):
                type_count[tag] = type_count.get(tag, 0) + 1

        # 预估总执行时间
        total_duration = sum(
            case.get("estimated_duration", 0)
            for case in test_cases
        )

        return {
            "test_cases": {
                "total": total_cases,
                "by_priority": priority_count,
                "by_type": type_count,
                "estimated_total_duration": total_duration
            },
            "exploration": {
                "pages_explored": total_pages,
                "elements_discovered": total_elements
            },
            "coverage": coverage_report.get("summary", {})
        }
