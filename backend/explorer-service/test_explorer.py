"""
探索引擎测试
测试网站探索引擎的核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from state_machine import PageStateMachine, PageState
from page_crawler import PageCrawler
from navigation_strategy import NavigationPlanner, AdaptiveNavigator, NavigationStrategy
from explorer import WebExplorer, ExploreSession


class TestPageStateMachine:
    """页面状态机测试"""

    def test_initialization(self):
        """测试状态机初始化"""
        sm = PageStateMachine(max_depth=3, max_pages=20)
        assert sm.max_depth == 3
        assert sm.max_pages == 20
        assert len(sm.pages) == 0
        assert len(sm.visited_urls) == 0

    def test_add_page(self):
        """测试添加页面"""
        sm = PageStateMachine(max_depth=3, max_pages=20)
        page = sm.add_page("http://example.com", 0)

        assert "http://example.com" in sm.pages
        assert page.depth == 0
        assert not page.visited

    def test_mark_visited(self):
        """测试标记页面为已访问"""
        sm = PageStateMachine(max_depth=3, max_pages=20)
        sm.add_page("http://example.com", 0)
        sm.mark_visited("http://example.com", "<html>test</html>")

        assert sm.is_explored("http://example.com")
        assert len(sm.visited_urls) == 1

    def test_duplicate_detection(self):
        """测试重复内容检测"""
        sm = PageStateMachine(max_depth=3, max_pages=20)
        sm.add_page("http://example.com/page1", 0)
        sm.mark_visited("http://example.com/page1", "<html>content</html>")

        # 相同内容应该被识别为重复
        assert sm.is_duplicate_content("<html>content</html>")

    def test_queue_management(self):
        """测试队列管理"""
        sm = PageStateMachine(max_depth=3, max_pages=20)

        # 添加页面到队列
        sm.add_to_queue("http://example.com/page1", "")
        sm.add_to_queue("http://example.com/page2", "")

        assert len(sm.exploration_queue) == 2

        # 获取下一页面
        next_page = sm.get_next_page()
        assert next_page is not None
        assert next_page[0] == "http://example.com/page1"

    def test_max_pages_limit(self):
        """测试最大页面数限制"""
        sm = PageStateMachine(max_depth=3, max_pages=2)

        # 尝试添加超过限制的页面
        sm.add_to_queue("http://example.com/page1", "")
        sm.add_to_queue("http://example.com/page2", "")
        sm.add_to_queue("http://example.com/page3", "")

        # 队列应该只包含max_pages个页面
        assert len(sm.exploration_queue) == 2

    def test_should_continue(self):
        """测试是否应该继续探索"""
        sm = PageStateMachine(max_depth=3, max_pages=20)

        # 初始状态应该继续
        assert sm.should_continue()

        # 添加一个页面但不访问
        sm.add_to_queue("http://example.com/page1", "")
        assert sm.should_continue()

        # 访问后应该继续（还有容量）
        sm.mark_visited("http://example.com/page1", "<html></html>")
        assert sm.should_continue()

    def test_exploration_stats(self):
        """测试探索统计"""
        sm = PageStateMachine(max_depth=3, max_pages=20)

        sm.add_page("http://example.com/page1", 0)
        sm.add_page("http://example.com/page2", 1)
        sm.add_page("http://example.com/page3", 1)

        stats = sm.get_exploration_stats()
        assert stats["total_pages"] == 3
        assert stats["visited_pages"] == 0
        assert stats["max_depth"] == 3
        assert stats["pages_at_depth"][0] == 1
        assert stats["pages_at_depth"][1] == 2


class TestNavigationStrategy:
    """导航策略测试"""

    def test_initialization(self):
        """测试导航规划器初始化"""
        planner = NavigationPlanner(NavigationStrategy.BFS)
        assert planner.strategy == NavigationStrategy.BFS

    def test_link_priority_calculation(self):
        """测试链接优先级计算"""
        planner = NavigationPlanner(NavigationStrategy.MIXED)

        # 登录链接应该有高优先级
        login_link = {
            "url": "http://example.com/login",
            "text": "Login",
            "type": "internal",
            "depth": 0
        }
        login_score = planner.calculate_link_priority(login_link)
        assert login_score > 0

        # 外部链接应该有低优先级
        external_link = {
            "url": "http://other-site.com",
            "text": "External",
            "type": "external",
            "depth": 0
        }
        external_score = planner.calculate_link_priority(external_link)
        assert login_score > external_score

    def test_should_explore_link(self):
        """测试链接是否应该被探索"""
        planner = NavigationPlanner(NavigationStrategy.MIXED)

        # 普通链接应该被探索
        normal_link = {"url": "http://example.com/page", "text": "Page"}
        assert planner.should_explore_link(normal_link)

        # JavaScript链接不应该被探索
        js_link = {"url": "javascript:void(0)", "text": "Click"}
        assert not planner.should_explore_link(js_link)

        # 注销链接不应该被探索
        logout_link = {"url": "http://example.com/logout", "text": "Logout"}
        assert not planner.should_explore_link(logout_link)

    def test_bfs_sorting(self):
        """测试BFS排序"""
        planner = NavigationPlanner(NavigationStrategy.BFS)

        links = [
            {"url": "http://example.com/page1", "depth": 0},
            {"url": "http://example.com/page2", "depth": 1},
            {"url": "http://example.com/page3", "depth": 0},
            {"url": "http://example.com/page4", "depth": 2},
        ]

        sorted_links = planner.sort_links_by_strategy(links, current_depth=0, max_depth=3)

        # BFS应该优先探索深度0的页面
        assert sorted_links[0]["depth"] == 0
        assert sorted_links[1]["depth"] == 0

    def test_dfs_sorting(self):
        """测试DFS排序"""
        planner = NavigationPlanner(NavigationStrategy.DFS)

        links = [
            {"url": "http://example.com/page1", "depth": 0},
            {"url": "http://example.com/page2", "depth": 1},
            {"url": "http://example.com/page3", "depth": 2},
            {"url": "http://example.com/page4", "depth": 0},
        ]

        sorted_links = planner.sort_links_by_strategy(links, current_depth=0, max_depth=3)

        # DFS应该优先探索深度大的页面
        depths = [l["depth"] for l in sorted_links]
        assert depths == sorted(depths, reverse=True)

    def test_generate_test_suggestions(self):
        """测试生成测试建议"""
        planner = NavigationPlanner(NavigationStrategy.MIXED)

        page_data = {
            "links": [
                {"url": "http://example.com/page1", "text": "Link 1"},
                {"url": "http://example.com/page2", "text": "Link 2"},
            ],
            "forms": [
                {
                    "action": "http://example.com/login",
                    "method": "POST",
                    "selector": "#login-form",
                    "fields": [
                        {"type": "text", "name": "username"},
                        {"type": "password", "name": "password"},
                    ]
                }
            ]
        }

        suggestions = planner.generate_test_suggestions(page_data)

        # 应该生成表单测试建议
        form_suggestions = [s for s in suggestions if s["type"] == "form_test"]
        assert len(form_suggestions) > 0


class TestPageCrawler:
    """页面爬虫测试"""

    def test_initialization(self):
        """测试爬虫初始化"""
        crawler = PageCrawler("http://example.com")
        assert crawler.base_url == "http://example.com"
        assert crawler.base_domain == "example.com"

    def test_is_internal_link(self):
        """测试内部链接判断"""
        crawler = PageCrawler("http://example.com")

        assert crawler.is_internal_link("http://example.com/page")
        assert crawler.is_internal_link("/page")
        assert not crawler.is_internal_link("http://other-site.com")

    def test_normalize_url(self):
        """测试URL标准化"""
        crawler = PageCrawler("http://example.com")

        # 相对URL
        assert crawler.normalize_url("/page") == "http://example.com/page"

        # 绝对URL
        assert crawler.normalize_url("http://example.com/page") == "http://example.com/page"

        # 锚点应该返回None
        assert crawler.normalize_url("#section") is None

        # JavaScript链接应该返回None
        assert crawler.normalize_url("javascript:alert(1)") is None

    def test_should_ignore_url(self):
        """测试URL是否应该被忽略"""
        crawler = PageCrawler("http://example.com")

        # PDF文件应该被忽略
        assert crawler.should_ignore_url("http://example.com/file.pdf")

        # JavaScript链接应该被忽略
        assert crawler.should_ignore_url("javascript:void(0)")

        # 注销链接应该被忽略
        assert crawler.should_ignore_url("http://example.com/logout")

        # 普通链接不应该被忽略
        assert not crawler.should_ignore_url("http://example.com/page")


class TestWebExplorer:
    """网站探索引擎测试"""

    def test_create_session(self):
        """测试创建探索会话"""
        explorer = WebExplorer(max_depth=2, max_pages=10)
        explore_id = explorer.create_session("http://example.com")

        assert explore_id in explorer.sessions
        assert explorer.sessions[explore_id].start_url == "http://example.com"
        assert explorer.sessions[explore_id].status == "pending"

    def test_get_session_status(self):
        """测试获取会话状态"""
        explorer = WebExplorer(max_depth=2, max_pages=10)
        explore_id = explorer.create_session("http://example.com")

        # 注意：这是同步方法，但在实际实现中需要用async
        status = explorer.sessions[explore_id].to_dict()

        assert status["explore_id"] == explore_id
        assert status["start_url"] == "http://example.com"

    def test_get_exploration_results(self):
        """测试获取探索结果"""
        explorer = WebExplorer(max_depth=2, max_pages=10)
        explore_id = explorer.create_session("http://example.com")

        # 添加一些页面数据
        explorer.state_machine.add_page("http://example.com/page1", 0)
        explorer.state_machine.add_page("http://example.com/page2", 1)

        results = explorer.get_exploration_results(explore_id)

        assert "session" in results
        assert "pages" in results
        assert len(results["pages"]) == 2


# 运行测试的入口
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
