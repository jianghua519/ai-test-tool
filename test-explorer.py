#!/usr/bin/env python3
"""
探索服务测试脚本
测试网页探索和用例生成功能
"""

import requests
import json
import time

def test_explorer_service():
    """测试探索服务"""
    print("=== 测试探索服务 ===")

    # 测试网页探索
    explore_data = {
        "url": "https://example.com",
        "maxPages": 2,
        "clickSelectors": ["a", "button"],
        "waitTime": 2
    }

    try:
        print("开始探索网页...")
        response = requests.post(
            "http://localhost:8004/api/explore",
            json=explore_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ 探索成功")
            print(f"  发现页面数: {result.get('pagesFound', 0)}")
            print(f"  生成用例数: {result.get('casesGenerated', 0)}")

            # 显示生成的测试用例
            if 'testCases' in result and result['testCases']:
                print("\n生成的测试用例:")
                for i, case in enumerate(result['testCases'][:3]):  # 只显示前3个
                    print(f"\n用例 {i+1}:")
                    print(f"  名称: {case.get('name')}")
                    print(f"  步骤数: {len(case.get('steps', []))}")
                    for step in case.get('steps', [])[:2]:  # 只显示前2步
                        print(f"    - {step.get('description')}")
        else:
            print(f"✗ 探索失败: {response.status_code}")
            print(f"  响应: {response.text}")

    except requests.exceptions.Timeout:
        print("✗ 探索超时")
    except Exception as e:
        print(f"✗ 探索错误: {str(e)}")

def test_ai_service():
    """测试AI服务"""
    print("\n=== 测试AI服务 ===")

    # 测试AI用例生成
    ai_request = {
        "prompt": "为登录页面生成一个测试用例",
        "context": {
            "url": "https://example.com/login",
            "elements": ["username", "password", "login button"]
        }
    }

    try:
        print("生成AI测试用例...")
        response = requests.post(
            "http://localhost:8003/api/generate-case",
            json=ai_request,
            headers={"Content-Type": "application/json"},
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ AI用例生成成功")
            print(f"  响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"✗ AI用例生成失败: {response.status_code}")
            print(f"  响应: {response.text}")

    except Exception as e:
        print(f"✗ AI服务错误: {str(e)}")

if __name__ == "__main__":
    print("AI Test Tool - 探索服务测试")
    print("=" * 40)

    # 等待服务启动
    time.sleep(2)

    test_explorer_service()
    test_ai_service()

    print("\n测试完成！")