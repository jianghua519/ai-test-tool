"""
页面状态机
用于记录和管理网站探索过程中的页面状态和访问路径
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import deque
import hashlib
import json


class PageState:
    """表示单个页面状态"""

    def __init__(self, url: str, depth: int, parent_url: Optional[str] = None):
        self.url = url
        self.depth = depth
        self.parent_url = parent_url
        self.visited = False
        self.dom_fingerprint = None
        self.elements_found = 0
        self.links_found = []
        self.forms_found = []
        self.interactive_elements = []

    def set_dom_fingerprint(self, dom_content: str):
        """生成DOM指纹用于去重"""
        # 简化：使用URL和页面内容的哈希
        content_hash = hashlib.md5(dom_content.encode('utf-8')).hexdigest()[:16]
        self.dom_fingerprint = content_hash

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "url": self.url,
            "depth": self.depth,
            "parent_url": self.parent_url,
            "visited": self.visited,
            "dom_fingerprint": self.dom_fingerprint,
            "elements_found": self.elements_found,
            "links_count": len(self.links_found),
            "forms_count": len(self.forms_found),
            "interactive_elements_count": len(self.interactive_elements)
        }


class PageStateMachine:
    """页面状态机，管理探索过程"""

    def __init__(self, max_depth: int = 3, max_pages: int = 20):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.pages: Dict[str, PageState] = {}  # URL -> PageState
        self.visited_urls: Set[str] = set()
        self.visited_fingerprints: Set[str] = set()
        self.exploration_queue: deque[Tuple[str, str]] = deque()  # (url, parent_url)
        self.exploration_path: List[str] = []  # 当前探索路径
        self.current_depth = 0

    def add_page(self, url: str, depth: int, parent_url: Optional[str] = None) -> PageState:
        """添加页面到状态机"""
        if url not in self.pages:
            page = PageState(url, depth, parent_url)
            self.pages[url] = page
        return self.pages[url]

    def mark_visited(self, url: str, dom_content: Optional[str] = None):
        """标记页面为已访问"""
        if url in self.pages:
            self.pages[url].visited = True
            self.visited_urls.add(url)
            if dom_content:
                self.pages[url].set_dom_fingerprint(dom_content)
                if self.pages[url].dom_fingerprint:
                    self.visited_fingerprints.add(self.pages[url].dom_fingerprint)

    def add_to_queue(self, url: str, parent_url: str):
        """添加页面到探索队列"""
        if url not in self.visited_urls and len(self.exploration_queue) < self.max_pages:
            self.exploration_queue.append((url, parent_url))

    def get_next_page(self) -> Optional[Tuple[str, str]]:
        """从队列获取下一个要探索的页面"""
        if self.exploration_queue:
            return self.exploration_queue.popleft()
        return None

    def is_explored(self, url: str) -> bool:
        """检查页面是否已被探索"""
        return url in self.visited_urls

    def is_duplicate_content(self, dom_content: str) -> bool:
        """检查内容是否重复"""
        fingerprint = hashlib.md5(dom_content.encode('utf-8')).hexdigest()[:16]
        return fingerprint in self.visited_fingerprints

    def get_exploration_stats(self) -> dict:
        """获取探索统计信息"""
        return {
            "total_pages": len(self.pages),
            "visited_pages": len(self.visited_urls),
            "queued_pages": len(self.exploration_queue),
            "max_depth": self.max_depth,
            "current_depth": self.current_depth,
            "pages_at_depth": self._count_pages_by_depth()
        }

    def _count_pages_by_depth(self) -> Dict[int, int]:
        """统计各深度的页面数量"""
        depth_count = {}
        for page in self.pages.values():
            depth_count[page.depth] = depth_count.get(page.depth, 0) + 1
        return depth_count

    def should_continue(self) -> bool:
        """判断是否应该继续探索"""
        return (
            len(self.exploration_queue) > 0 and
            len(self.visited_urls) < self.max_pages
        )

    def get_exploration_path(self, target_url: str) -> List[str]:
        """获取到达目标页面的探索路径"""
        path = []
        current_url = target_url
        visited_set = set()

        while current_url and current_url not in visited_set:
            visited_set.add(current_url)
            path.append(current_url)
            if current_url in self.pages and self.pages[current_url].parent_url:
                current_url = self.pages[current_url].parent_url
            else:
                break

        return list(reversed(path))

    def export_to_json(self) -> str:
        """导出状态为JSON"""
        data = {
            "stats": self.get_exploration_stats(),
            "pages": [page.to_dict() for page in self.pages.values()],
            "visited_urls": list(self.visited_urls),
            "queue": list(self.exploration_queue)[:10]  # 只显示前10个
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
