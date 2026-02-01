"""
自动网站探索引擎
核心探索逻辑，集成页面爬虫、导航策略和状态机
"""

import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import json
import uuid
from datetime import datetime

from state_machine import PageStateMachine, PageState
from page_crawler import PageCrawler
from navigation_strategy import NavigationPlanner, AdaptiveNavigator
from case_generator import TestCaseGenerator
from case_deduplicator import CaseDeduplicator
from coverage_reporter import CoverageReporter


@dataclass
class ExploreSession:
    """探索会话信息"""
    explore_id: str
    start_url: str
    max_depth: int
    max_pages: int
    strategy: str
    status: str  # 'pending', 'running', 'paused', 'completed', 'error'
    start_time: datetime
    end_time: Optional[datetime] = None
    pages_explored: int = 0
    elements_found: int = 0
    cases_generated: int = 0
    current_url: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "explore_id": self.explore_id,
            "start_url": self.start_url,
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "strategy": self.strategy,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "pages_explored": self.pages_explored,
            "elements_found": self.elements_found,
            "cases_generated": self.cases_generated,
            "current_url": self.current_url,
            "error": self.error
        }


class WebExplorer:
    """网站探索引擎"""

    def __init__(self, max_depth: int = 3, max_pages: int = 20, strategy: str = "mixed"):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.strategy = strategy
        self.state_machine = PageStateMachine(max_depth, max_pages)
        self.navigator = AdaptiveNavigator()
        self.sessions: Dict[str, ExploreSession] = {}
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.case_generator = TestCaseGenerator()
        self.case_deduplicator = CaseDeduplicator()
        self.coverage_reporter = CoverageReporter()

    async def initialize(self):
        """初始化浏览器"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()

    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    def create_session(self, start_url: str, strategy: str = "mixed") -> str:
        """创建探索会话"""
        explore_id = str(uuid.uuid4())

        session = ExploreSession(
            explore_id=explore_id,
            start_url=start_url,
            max_depth=self.max_depth,
            max_pages=self.max_pages,
            strategy=strategy,
            status="pending",
            start_time=datetime.now()
        )

        self.sessions[explore_id] = session
        return explore_id

    async def explore(self, explore_id: str) -> Dict[str, Any]:
        """执行探索"""
        if explore_id not in self.sessions:
            raise ValueError(f"Session {explore_id} not found")

        session = self.sessions[explore_id]
        session.status = "running"
        session.start_url = session.start_url or session.start_url

        try:
            await self.initialize()

            # 添加起始页面
            self.state_machine.add_page(session.start_url, 0)
            self.state_machine.add_to_queue(session.start_url, "")

            total_elements = 0
            discovered_cases = []

            # 开始探索循环
            while self.state_machine.should_continue():
                next_page = self.state_machine.get_next_page()
                if not next_page:
                    break

                url, parent_url = next_page
                depth = self.state_machine.pages[url].depth if url in self.state_machine.pages else 0

                if depth > self.max_depth:
                    continue

                session.current_url = url

                # 导航到页面
                try:
                    await self.page.goto(url, wait_until="networkidle", timeout=10000)

                    # 等待页面加载
                    await asyncio.sleep(1)

                    # 获取页面内容
                    content = await self.page.content()

                    # 检查重复内容
                    if self.state_machine.is_duplicate_content(content):
                        continue

                    # 标记为已访问
                    self.state_machine.mark_visited(url, content)
                    session.pages_explored = len(self.state_machine.visited_urls)

                    # 使用爬虫分析页面
                    crawler = PageCrawler(url)
                    page_data = await crawler.analyze_page(self.page, url)

                    # 更新统计
                    total_elements += page_data.get("stats", {}).get("interactive_elements_count", 0)
                    session.elements_found = total_elements

                    # 发现新链接并添加到队列
                    for link in page_data.get("links", []):
                        link_url = link.get("url")
                        if link_url and not self.state_machine.is_explored(link_url):
                            link_depth = depth + 1
                            self.state_machine.add_page(link_url, link_depth, url)

                            # 根据策略决定是否添加到队列
                            if self.navigator.planner.should_explore_link(link.__dict__):
                                self.state_machine.add_to_queue(link_url, url)

                    # 生成测试建议
                    suggestions = self.navigator.planner.generate_test_suggestions(page_data)
                    for suggestion in suggestions:
                        if suggestion not in discovered_cases:
                            discovered_cases.append(suggestion)

                    # 更新页面信息
                    if url in self.state_machine.pages:
                        page_state = self.state_machine.pages[url]
                        page_state.links_found = [l.url for l in page_data.get("links", [])]
                        page_state.forms_found = page_data.get("forms", [])
                        page_state.interactive_elements = page_data.get("interactive_elements", [])

                except Exception as e:
                    print(f"Error exploring {url}: {e}")
                    continue

            # 生成测试用例
            session.cases_generated = len(discovered_cases)

            session.status = "completed"
            session.end_time = datetime.now()
            session.current_url = None

            return {
                "status": "completed",
                "explore_id": explore_id,
                "pages_explored": session.pages_explored,
                "elements_found": session.elements_found,
                "cases_generated": session.cases_generated,
                "discovered_cases": discovered_cases,
                "exploration_stats": self.state_machine.get_exploration_stats()
            }

        except Exception as e:
            session.status = "error"
            session.error = str(e)
            session.end_time = datetime.now()
            raise e

    async def get_session_status(self, explore_id: str) -> Dict[str, Any]:
        """获取探索会话状态"""
        if explore_id not in self.sessions:
            raise ValueError(f"Session {explore_id} not found")

        session = self.sessions[explore_id]
        return session.to_dict()

    async def pause_explore(self, explore_id: str):
        """暂停探索"""
        if explore_id in self.sessions:
            self.sessions[explore_id].status = "paused"

    async def resume_explore(self, explore_id: str):
        """恢复探索"""
        if explore_id in self.sessions and self.sessions[explore_id].status == "paused":
            self.sessions[explore_id].status = "running"
            return await self.explore(explore_id)

    async def stop_explore(self, explore_id: str):
        """停止探索"""
        if explore_id in self.sessions:
            self.sessions[explore_id].status = "completed"
            self.sessions[explore_id].end_time = datetime.now()

    def get_exploration_results(self, explore_id: str) -> Dict[str, Any]:
        """获取探索结果"""
        if explore_id not in self.sessions:
            raise ValueError(f"Session {explore_id} not found")

        session = self.sessions[explore_id]

        return {
            "session": session.to_dict(),
            "state_machine": self.state_machine.export_to_json(),
            "pages": [page.to_dict() for page in self.state_machine.pages.values()]
        }

    def generate_test_cases(self, explore_id: str) -> Dict[str, Any]:
        """生成测试用例"""
        if explore_id not in self.sessions:
            raise ValueError(f"Session {explore_id} not found")

        exploration_results = self.get_exploration_results(explore_id)

        # 使用用例生成器生成测试用例
        cases = self.case_generator.generate_cases_from_exploration(exploration_results)

        # 去重
        deduplicated_cases = self.case_deduplicator.deduplicate_cases(cases)

        # 计算覆盖度
        coverage_report = self.coverage_reporter.calculate_coverage(
            exploration_results,
            deduplicated_cases
        )

        # 更新会话信息
        self.sessions[explore_id].cases_generated = len(deduplicated_cases)

        return {
            "explore_id": explore_id,
            "test_cases": deduplicated_cases,
            "total_cases": len(deduplicated_cases),
            "coverage_report": coverage_report,
            "summary": {
                "pages_explored": exploration_results["session"]["pages_explored"],
                "elements_found": exploration_results["session"]["elements_found"],
                "cases_generated": len(deduplicated_cases)
            }
        }

    def generate_coverage_report(self, explore_id: str) -> Dict[str, Any]:
        """生成覆盖度报告"""
        if explore_id not in self.sessions:
            raise ValueError(f"Session {explore_id} not found")

        exploration_results = self.get_exploration_results(explore_id)

        # 获取已生成的测试用例
        # 这里应该从数据库或缓存中获取，简化处理
        test_cases = self.case_generator.generated_cases

        # 计算覆盖度
        coverage_report = self.coverage_reporter.calculate_coverage(
            exploration_results,
            [c.to_dict() for c in test_cases]
        )

        return coverage_report

    def export_test_cases(self, explore_id: str, format: str = "json") -> str:
        """导出测试用例"""
        if explore_id not in self.sessions:
            raise ValueError(f"Session {explore_id} not found")

        # 重新生成测试用例
        result = self.generate_test_cases(explore_id)

        if format == "json":
            return json.dumps(result, indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._export_to_markdown(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_to_markdown(self, result: Dict[str, Any]) -> str:
        """导出为Markdown格式"""
        lines = []

        lines.append("# 自动生成的测试用例")
        lines.append("")
        lines.append(f"**探索ID**: {result['explore_id']}")
        lines.append(f"**用例数量**: {result['total_cases']}")
        lines.append("")

        # 用例列表
        for i, case in enumerate(result["test_cases"], 1):
            lines.append(f"## 用例 {i}: {case['name']}")
            lines.append("")
            lines.append(f"**描述**: {case['description']}")
            lines.append(f"**优先级**: {case['priority']}")
            lines.append(f"**标签**: {', '.join(case['tags'])}")
            lines.append("")
            lines.append("### 步骤")
            lines.append("")

            for j, step in enumerate(case["steps"], 1):
                lines.append(f"{j}. **{step['name']}**")
                lines.append(f"   - 动作: {step['action']}")
                if step.get("value"):
                    lines.append(f"   - 值: {step['value']}")
                if step.get("selector"):
                    lines.append(f"   - 选择器: `{step['selector']}`")

            lines.append("")
            lines.append("### 断言")
            lines.append("")

            for assertion in case["assertions"]:
                lines.append(f"- **{assertion['type']}**: {assertion['description']}")

            lines.append("")

        # 覆盖度报告
        lines.append("## 覆盖度报告")
        lines.append("")

        coverage = result["coverage_report"]["summary"]
        lines.append(f"- **平均覆盖度**: {coverage['average_coverage']}%")
        lines.append(f"- **状态**: {coverage['status']}")
        lines.append("")

        for metric in result["coverage_report"]["metrics"]:
            lines.append(f"### {metric['metric']}")
            lines.append("")
            lines.append(f"- **覆盖**: {metric['covered']} / {metric['total']}")
            lines.append(f"- **百分比**: {metric['percentage']}%")

        return "\n".join(lines)


# 全局探索器实例
_explorer_instance: Optional[WebExplorer] = None


def get_explorer() -> WebExplorer:
    """获取全局探索器实例"""
    global _explorer_instance
    if _explorer_instance is None:
        _explorer_instance = WebExplorer()
    return _explorer_instance


async def cleanup_explorer():
    """清理探索器"""
    global _explorer_instance
    if _explorer_instance:
        await _explorer_instance.close()
        _explorer_instance = None
