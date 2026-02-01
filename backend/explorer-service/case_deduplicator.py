"""
用例去重器
合并相似测试路径，去除重复用例
"""

from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass
import hashlib


@dataclass
class CaseSignature:
    """用例签名，用于去重"""
    name_hash: str
    steps_hash: str
    signature: str
    tags: Set[str]


class CaseDeduplicator:
    """用例去重器"""

    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold

    def deduplicate_cases(
        self,
        cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重测试用例"""
        if not cases:
            return []

        # 生成所有用例的签名
        signatures = [self._generate_signature(case) for case in cases]

        # 按相似性分组
        groups = self._group_by_similarity(cases, signatures)

        # 从每组中选择最佳用例
        unique_cases = []
        for group in groups:
            if len(group) == 1:
                unique_cases.append(group[0])
            else:
                # 选择优先级最高、步骤最完整的用例
                best_case = self._select_best_case(group)
                unique_cases.append(best_case)

        return unique_cases

    def _generate_signature(self, case: Dict[str, Any]) -> CaseSignature:
        """生成用例签名"""
        # 用例名称哈希
        name = case.get("name", "")
        name_hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]

        # 步骤哈希（基于选择器）
        steps = case.get("steps", [])
        selectors = [step.get("selector", "") for step in steps]
        steps_hash = hashlib.md5("|".join(selectors).encode('utf-8')).hexdigest()[:12]

        # 完整签名
        signature_data = f"{name}|{steps_hash}"
        signature = hashlib.md5(signature_data.encode('utf-8')).hexdigest()

        # 标签集合
        tags = set(case.get("tags", []))

        return CaseSignature(
            name_hash=name_hash,
            steps_hash=steps_hash,
            signature=signature,
            tags=tags
        )

    def _group_by_similarity(
        self,
        cases: List[Dict[str, Any]],
        signatures: List[CaseSignature]
    ) -> List[List[Dict[str, Any]]]:
        """按相似性分组用例"""
        groups: List[List[Dict[str, Any]]] []
        seen_signatures: Set[str] = set()

        for case, sig in zip(cases, signatures):
            # 检查是否与现有组相似
            found_group = False
            for group in groups:
                # 检查与组中第一个用例的相似度
                if self._are_similar(case, group[0]):
                    group.append(case)
                    found_group = True
                    break

            if not found_group and sig.signature not in seen_signatures:
                groups.append([case])
                seen_signatures.add(sig.signature)

        return groups

    def _are_similar(
        self,
        case1: Dict[str, Any],
        case2: Dict[str, Any]
    ) -> bool:
        """判断两个用例是否相似"""
        # 1. 检查名称相似度
        name1 = case1.get("name", "").lower()
        name2 = case2.get("name", "").lower()
        name_similarity = self._calculate_similarity(name1, name2)

        # 2. 检查步骤相似度
        steps1 = case1.get("steps", [])
        steps2 = case2.get("steps", [])

        if len(steps1) == 0 and len(steps2) == 0:
            return True

        steps_similarity = self._calculate_steps_similarity(steps1, steps2)

        # 3. 检查标签重叠
        tags1 = set(case1.get("tags", []))
        tags2 = set(case2.get("tags", []))
        tag_overlap = len(tags1 & tags2)
        tag_total = len(tags1 | tags2)
        tag_similarity = tag_overlap / tag_total if tag_total > 0 else 0

        # 综合相似度
        overall_similarity = (
            name_similarity * 0.3 +
            steps_similarity * 0.5 +
            tag_similarity * 0.2
        )

        return overall_similarity >= self.similarity_threshold

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0

        # 简单的编辑距离相似度
        distance = self._levenshtein_distance(str1, str2)
        max_len = max(len(str1), len(str2))
        return 1.0 - (distance / max_len)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算Levenshtein距离"""
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    cost = 0
                else:
                    cost = 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,     # 删除
                    dp[i][j - 1] + 1,     # 插入
                    dp[i - 1][j - 1] + cost  # 替换
                )

        return dp[m][n]

    def _calculate_steps_similarity(
        self,
        steps1: List[Dict[str, Any]],
        steps2: List[Dict[str, Any]]
    ) -> float:
        """计算步骤相似度"""
        if len(steps1) == 0 and len(steps2) == 0:
            return 1.0
        if len(steps1) == 0 or len(steps2) == 0:
            return 0.0

        # 提取选择器序列
        selectors1 = [s.get("selector", "") for s in steps1]
        selectors2 = [s.get("selector", "") for s in steps2]

        # 计算最长公共子序列
        lcs_length = self._longest_common_subsequence(selectors1, selectors2)

        # 相似度 = LCS长度 / 最大长度
        max_length = max(len(selectors1), len(selectors2))
        return lcs_length / max_length if max_length > 0 else 0

    def _longest_common_subsequence(
        self,
        list1: List[str],
        list2: List[str]
    ) -> int:
        """计算最长公共子序列长度"""
        m, n = len(list1), len(list2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if list1[i - 1] == list2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    def _select_best_case(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从相似用例组中选择最佳用例"""
        # 选择标准：
        # 1. 优先级最高
        # 2. 步骤数最多（覆盖最全面）
        # 3. 断言最多

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        best_case = max(
            cases,
            key=lambda c: (
                -priority_order.get(c.get("priority", "medium"), 2),  # 优先级（负值用于降序）
                len(c.get("steps", [])),  # 步骤数
                len(c.get("assertions", []))  # 断言数
            )
        )

        return best_case

    def merge_cases(
        self,
        cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并相似的用例"""
        # 先去重
        unique_cases = self.deduplicate_cases(cases)

        # 检查是否有可以合并的用例
        merged_cases = []
        while unique_cases:
            current = unique_cases.pop(0)
            merged = False

            for i, existing in enumerate(merged_cases):
                # 检查是否可以合并（相同标签，类似名称）
                if self._should_merge(current, existing):
                    # 合并用例：合并标签，保留更长的步骤序列
                    merged_case = self._merge_two_cases(current, existing)
                    merged_cases[i] = merged_case
                    merged = True
                    break

            if not merged:
                merged_cases.append(current)

        return merged_cases

    def _should_merge(
        self,
        case1: Dict[str, Any],
        case2: Dict[str, Any]
    ) -> bool:
        """判断两个用例是否应该合并"""
        # 合并条件：相同标签，步骤序列是子集关系
        tags1 = set(case1.get("tags", []))
        tags2 = set(case2.get("tags", []))

        # 至少有一个共同标签
        if not (tags1 & tags2):
            return False

        # 步骤序列应该有明显的子集关系
        steps1 = case1.get("steps", [])
        steps2 = case2.get("steps", [])

        # 检查steps1是否是steps2的子序列，或反之
        return self._is_subsequence(steps1, steps2) or self._is_subsequence(steps2, steps1)

    def _is_subsequence(
        self,
        steps1: List[Dict[str, Any]],
        steps2: List[Dict[str, Any]]
    ) -> bool:
        """检查steps1是否是steps2的子序列"""
        selectors1 = [s.get("selector", "") for s in steps1]
        selectors2 = [s.get("selector", "") for s in steps2]

        # 简化：如果steps1的选择器都出现在steps2中，且顺序一致
        try:
            idx = 0
            for s in selectors1:
                idx = selectors2.index(s, idx) if s in selectors2[idx:] else -1
                if idx == -1:
                    return False
                idx += 1
            return True
        except:
            return False

    def _merge_two_cases(
        self,
        case1: Dict[str, Any],
        case2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并两个用例"""
        # 选择步骤更长的用例作为基础
        base_case = case1 if len(case1.get("steps", [])) >= len(case2.get("steps", [])) else case2
        other_case = case2 if base_case == case1 else case1

        # 合并标签
        merged_tags = list(set(base_case.get("tags", []) + other_case.get("tags", [])))

        # 合并断言
        merged_assertions = []
        base_assertions = {a.get("type") + str(a.get("value")) for a in base_case.get("assertions", [])}

        for assertion in base_case.get("assertions", []):
            merged_assertions.append(assertion)

        for assertion in other_case.get("assertions", []):
            key = assertion.get("type") + str(assertion.get("value"))
            if key not in base_assertions:
                merged_assertions.append(assertion)

        return {
            "name": base_case.get("name"),
            "description": base_case.get("description"),
            "priority": base_case.get("priority"),
            "steps": base_case.get("steps"),
            "assertions": merged_assertions,
            "tags": merged_tags,
            "estimated_duration": base_case.get("estimated_duration", 0) + other_case.get("estimated_duration", 0),
            "merged_from": [case1.get("name"), case2.get("name")]
        }
