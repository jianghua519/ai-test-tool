#!/usr/bin/env python3
"""
快速测试脚本 - 检查服务是否正常启动
"""

import requests
import json
import time
from datetime import datetime

print("=" * 50)
print("AI Test Tool - 快速服务测试")
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# 服务列表
services = [
    ("前端", "http://localhost:5173", None),
    ("API 网关", "http://localhost:3000", "/health"),
    ("用例服务", "http://localhost:8001", "/health"),
    ("执行服务", "http://localhost:3001", "/health"),
    ("报告服务", "http://localhost:8002", "/health"),
    ("AI 服务", "http://localhost:8003", "/health"),
    ("探索服务", "http://localhost:8004", "/health"),
]

# 等待服务启动
print("\n等待服务启动...")
time.sleep(2)

# 测试每个服务
all_ok = True
for name, url, endpoint in services:
    print(f"\n检查 {name}:")
    try:
        if endpoint:
            full_url = url + endpoint
        else:
            full_url = url

        response = requests.get(full_url, timeout=5)

        if response.status_code == 200:
            print(f"  ✓ {name} 正常 ({url})")
            if endpoint == "/health":
                try:
                    data = response.json()
                    print(f"    响应: {data}")
                except:
                    pass
        else:
            print(f"  ✗ {name} 响应异常: {response.status_code}")
            all_ok = False
    except requests.exceptions.ConnectionError:
        print(f"  ✗ {name} 连接失败")
        all_ok = False
    except requests.exceptions.Timeout:
        print(f"  ✗ {name} 请求超时")
        all_ok = False
    except Exception as e:
        print(f"  ✗ {name} 错误: {str(e)}")
        all_ok = False

# 总结
print("\n" + "=" * 50)
if all_ok:
    print("🎉 所有服务正常运行！")
else:
    print("⚠️  部分服务异常，请检查日志")
print("=" * 50)

# 测试用例服务 API
print("\n测试用例服务 API...")
try:
    # 创建测试用例
    test_case = {
        "name": "测试用例示例",
        "description": "这是一个测试用例",
        "steps": [
            {
                "type": "navigate",
                "url": "https://example.com",
                "description": "导航到示例网站"
            },
            {
                "type": "click",
                "selector": "button",
                "description": "点击按钮"
            }
        ]
    }

    response = requests.post(
        "http://localhost:8001/api/cases",
        json=test_case,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        print("✓ 创建测试用例成功")
        case_data = response.json()
        print(f"  用例ID: {case_data.get('id')}")

        # 获取用例列表
        response = requests.get("http://localhost:8001/api/cases")
        if response.status_code == 200:
            cases = response.json()
            print(f"✓ 获取用例列表成功，共 {len(cases)} 个用例")
    else:
        print(f"✗ 创建测试用例失败: {response.status_code}")

except Exception as e:
    print(f"✗ 测试用例服务 API 错误: {str(e)}")

print("\n测试完成！")