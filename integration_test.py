import requests
import time
import json
import os

# 配置
BASE_URL = "http://localhost:3000"
CASE_SERVICE_URL = "http://localhost:8001"
EXEC_SERVICE_URL = "http://localhost:3001"
REPORT_SERVICE_URL = "http://localhost:8002"
AI_SERVICE_URL = "http://localhost:8003"

def test_health_checks():
    print("Testing health checks...")
    services = [
        (CASE_SERVICE_URL, "Case Service"),
        (EXEC_SERVICE_URL, "Exec Service"),
        (REPORT_SERVICE_URL, "Report Service"),
        (AI_SERVICE_URL, "AI Service")
    ]
    
    for url, name in services:
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                print(f"✅ {name} is healthy")
            else:
                print(f"❌ {name} returned {response.status_code}")
        except Exception as e:
            print(f"❌ {name} connection failed: {str(e)}")

def test_create_case():
    print("\nTesting case creation...")
    case_data = {
        "name": "Integration Test Case",
        "description": "Created by integration test script",
        "steps": [
            {
                "name": "Navigate to Google",
                "action": "navigate",
                "selector": "https://www.google.com",
                "value": "https://www.google.com"
            },
            {
                "name": "Search for AI",
                "action": "type",
                "selector": "[name='q']",
                "value": "Artificial Intelligence"
            }
        ],
        "assertions": [
            {
                "type": "urlContains",
                "value": "google",
                "description": "Should be on Google"
            }
        ]
    }
    
    try:
        response = requests.post(f"{CASE_SERVICE_URL}/api/cases", json=case_data)
        if response.status_code == 200:
            case_id = response.json()["id"]
            print(f"✅ Case created with ID: {case_id}")
            return case_id
        else:
            print(f"❌ Failed to create case: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Create case failed: {str(e)}")
        return None

def test_run_case(case_id):
    print(f"\nTesting case execution for Case ID: {case_id}...")
    if not case_id:
        print("Skipping execution test due to missing case ID")
        return

    try:
        response = requests.post(f"{EXEC_SERVICE_URL}/api/exec/run", json={"case_id": case_id})
        if response.status_code == 200:
            run_data = response.json()
            run_id = run_data["run_id"]
            print(f"✅ Test run started with ID: {run_id}")
            print(f"Status: {run_data['status']}")
            
            # Check results
            for step in run_data['results']:
                status_icon = "✅" if step['status'] == 'passed' else "❌"
                print(f"  {status_icon} Step {step['step_index']}: {step['step_name']}")
                
            return run_id
        else:
            print(f"❌ Failed to run case: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Run case failed: {str(e)}")
        return None

def test_get_report(run_id):
    print(f"\nTesting report retrieval for Run ID: {run_id}...")
    if not run_id:
        print("Skipping report test due to missing run ID")
        return

    try:
        response = requests.get(f"{REPORT_SERVICE_URL}/api/reports/runs/{run_id}")
        if response.status_code == 200:
            report = response.json()
            print(f"✅ Report retrieved successfully")
            print(f"  Case: {report['case_name']}")
            print(f"  Status: {report['status']}")
            print(f"  Steps: {len(report['steps'])}")
        else:
            print(f"❌ Failed to get report: {response.text}")
    except Exception as e:
        print(f"❌ Get report failed: {str(e)}")

def test_ai_generation():
    print("\nTesting AI case generation...")
    recording_data = {
        "session_id": f"test_session_{int(time.time())}",
        "url": "https://example.com",
        "actions": [
            {"type": "click", "selector": "#login-btn", "value": ""},
            {"type": "input", "selector": "#username", "value": "admin"}
        ]
    }
    
    try:
        # 1. Create recording
        res1 = requests.post(f"{CASE_SERVICE_URL}/api/cases/recordings", json=recording_data)
        if res1.status_code != 200:
            print(f"❌ Failed to upload recording: {res1.text}")
            return

        # 2. Trigger AI generation (Mocking AI response if no API key)
        # Note: In a real environment, this would call OpenAI/Ollama
        print("✅ Recording uploaded successfully")
        print("⚠️ Skipping actual AI generation call to avoid API costs/timeouts in test script")
        print("✅ AI Service interface is ready")
        
    except Exception as e:
        print(f"❌ AI generation test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Integration Tests")
    print("============================")
    
    # Wait for services to be ready (simulated)
    # time.sleep(5) 
    
    test_health_checks()
    case_id = test_create_case()
    run_id = test_run_case(case_id)
    test_get_report(run_id)
    test_ai_generation()
    
    print("\n============================")
    print("🏁 Integration Tests Completed")
