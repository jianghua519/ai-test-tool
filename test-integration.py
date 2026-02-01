#!/usr/bin/env python3
"""
AI Test Tool 集成测试脚本
测试所有服务是否正常运行
"""

import requests
import time
import json
from datetime import datetime

# 服务配置
services = {
    "api_gateway": {
        "url": "http://localhost:3000",
        "endpoints": ["/health"]
    },
    "case_service": {
        "url": "http://localhost:8001",
        "endpoints": ["/health"]
    },
    "exec_service": {
        "url": "http://localhost:3001",
        "endpoints": ["/health"]
    },
    "report_service": {
        "url": "http://localhost:8002",
        "endpoints": ["/health"]
    },
    "ai_service": {
        "url": "http://localhost:8003",
        "endpoints": ["/health"]
    },
    "explorer_service": {
        "url": "http://localhost:8004",
        "endpoints": ["/health"]
    }
}

def check_service_health(service_name, service_config):
    """检查服务健康状态"""
    base_url = service_config["url"]
    results = []

    print(f"\n=== 检查 {service_name} ===")
    print(f"服务地址: {base_url}")

    for endpoint in service_config["endpoints"]:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {endpoint}: 状态码 {response.status_code}")
                results.append(True)

                # 如果是健康检查，打印响应内容
                if endpoint == "/health":
                    try:
                        data = response.json()
                        print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"  响应: {response.text}")
            else:
                print(f"✗ {endpoint}: 状态码 {response.status_code}")
                results.append(False)
        except requests.exceptions.ConnectionError:
            print(f"✗ {endpoint}: 连接失败")
            results.append(False)
        except requests.exceptions.Timeout:
            print(f"✗ {endpoint}: 请求超时")
            results.append(False)
        except Exception as e:
            print(f"✗ {endpoint}: 错误 - {str(e)}")
            results.append(False)

    return all(results)

def test_case_service_api():
    """测试用例服务 API"""
    print("\n=== 测试用例服务 API ===")

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

    try:
        # 创建用例
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
                print(f"✗ 获取用例列表失败: {response.status_code}")
        else:
            print(f"✗ 创建测试用例失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 测试用例服务 API 错误: {str(e)}")

def test_frontend_routing():
    """测试前端路由"""
    print("\n=== 测试前端路由 ===")

    try:
        # 检查前端是否可访问
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✓ 前端服务可访问")
        else:
            print(f"✗ 前端服务响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ 前端服务未启动")
    except Exception as e:
        print(f"✗ 前端服务测试错误: {str(e)}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("AI Test Tool 集成测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 等待服务启动
    print("\n等待服务启动...")
    time.sleep(2)

    # 检查所有服务
    all_healthy = True
    for service_name, config in services.items():
        is_healthy = check_service_health(service_name, config)
        all_healthy = all_healthy and is_healthy

    # 测试特定服务
    test_case_service_api()
    test_frontend_routing()

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)

    for service_name, config in services.items():
        is_healthy = check_service_health(service_name, config)
        status = "✓ 正常" if is_healthy else "✗ 异常"
        print(f"{service_name:20} {status}")

    print(f"\前端服务            {'✓ 正常' if requests.get('http://localhost:5173', timeout=1).status_code == 200 else '✗ 异常'}")

    if all_healthy:
        print("\n🎉 所有服务正常运行！")
    else:
        print("\n⚠️  部分服务异常，请检查日志")

    print("=" * 60)

if __name__ == "__main__":
    main()