import json

import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzYzNTA2NjE3fQ.CHfaDnY1x7Bbd6gA-9wrfjnzhld-gNz7A7W-w2tm69E"
ORG_ID = "1"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "X-Organization-Id": ORG_ID,
    "Content-Type": "application/json",
}


def log(msg, data=None):
    print(f"\n[TEST] {msg}")
    if data:
        print(json.dumps(data, indent=2))


def run():
    # 1. Create Deal
    print("--- Creating Deal ---")
    deal_payload = {"contact_id": 1, "title": "Big Sale", "amount": 5000.0, "currency": "USD"}
    resp = requests.post(f"{BASE_URL}/deals", json=deal_payload, headers=headers)
    log("Create Deal Status:", resp.status_code)
    if resp.status_code not in [200, 201]:
        log("Error:", resp.text)
        return
    deal_data = resp.json()
    log("Deal Created:", deal_data)
    deal_id = deal_data.get("id")

    # 2. Create Task
    print("\n--- Creating Task ---")
    task_payload = {
        "deal_id": deal_id,
        "title": "Call Client",
        "description": "Ask about money",
        "due_date": "2025-12-31",  # Future date
    }
    resp = requests.post(f"{BASE_URL}/tasks", json=task_payload, headers=headers)
    log("Create Task Status:", resp.status_code)
    log("Task Response:", resp.json())

    # 3. Patch Deal to WON
    print("\n--- Updating Deal to WON ---")
    patch_payload = {"status": "won", "stage": "closed"}
    resp = requests.patch(f"{BASE_URL}/deals/{deal_id}", json=patch_payload, headers=headers)
    log("Patch Deal Status:", resp.status_code)
    log("Patch Response:", resp.json())

    # 4. Check Activities
    print("\n--- Checking Activities ---")
    resp = requests.get(f"{BASE_URL}/deals/{deal_id}/activities", headers=headers)
    log("Activities Status:", resp.status_code)
    activities = resp.json()
    log("Activities:", activities)

    # Verify we have a status change activity
    has_status_change = any(
        a["type"] == "status_changed" or a["type"] == "stage_changed" for a in activities
    )
    print(f"Found status/stage change activity: {has_status_change}")

    # 5. Check Analytics
    print("\n--- Checking Analytics ---")
    resp = requests.get(f"{BASE_URL}/analytics/deals/summary", headers=headers)
    log("Analytics Status:", resp.status_code)
    log("Analytics Data:", resp.json())

    # 6. Check Funnel
    resp = requests.get(f"{BASE_URL}/analytics/deals/funnel", headers=headers)
    log("Funnel Status:", resp.status_code)
    log("Funnel Data:", resp.json())


if __name__ == "__main__":
    run()
