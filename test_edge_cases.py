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


def test_task_past_due():
    print("\n--- Test: Task with Past Due Date ---")
    # Assuming Deal ID 2 exists from previous test
    payload = {
        "deal_id": 2,
        "title": "Past Task",
        "description": "Should fail",
        "due_date": "2020-01-01",
    }
    resp = requests.post(f"{BASE_URL}/tasks", json=payload, headers=headers)
    log("Response Code:", resp.status_code)
    log("Response Body:", resp.json())
    if resp.status_code in [400, 422]:
        print("SUCCESS: Task creation rejected.")
    else:
        print("FAILURE: Task created unexpectedly.")


def test_won_deal_zero_amount():
    print("\n--- Test: Won Deal with Zero Amount ---")
    # Create deal with 0 amount
    deal_payload = {"contact_id": 1, "title": "Zero Value", "amount": 0, "currency": "USD"}
    resp = requests.post(f"{BASE_URL}/deals", json=deal_payload, headers=headers)
    if resp.status_code not in [200, 201]:
        log("Setup Failed: Could not create zero amount deal", resp.text)
        return

    deal_id = resp.json()["id"]

    # Try to patch to won
    patch_payload = {"status": "won"}
    resp = requests.patch(f"{BASE_URL}/deals/{deal_id}", json=patch_payload, headers=headers)
    log("Response Code:", resp.status_code)
    log("Response Body:", resp.json())

    if resp.status_code == 400:  # TZ says 400
        print("SUCCESS: Won transition rejected.")
    else:
        print("FAILURE: Won transition accepted unexpectedly.")


def test_delete_contact_with_deals():
    print("\n--- Test: Delete Contact with Active Deals ---")
    # Use Contact 1 which has deals from previous test
    resp = requests.delete(f"{BASE_URL}/contacts/1", headers=headers)
    log("Response Code:", resp.status_code)

    if resp.status_code == 409:  # TZ says 409
        print("SUCCESS: Deletion rejected.")
    else:
        print(f"FAILURE: Deletion status {resp.status_code}")


def test_cross_tenant_access():
    print("\n--- Test: Cross Tenant Access ---")

    import time

    # Let's register User 2
    reg_payload = {
        "email": f"spy_{int(time.time())}@example.com",
        "password": "password123",
        "name": "Spy",
        "organization_name": f"Spy Corp {int(time.time())}",
    }
    resp = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
    if resp.status_code != 200:
        log("Setup Failed: Could not register spy", resp.text)
        return

    spy_token = resp.json()["access_token"]

    spy_headers = {
        "Authorization": f"Bearer {spy_token}",
        "X-Organization-Id": "2",  # Guessing ID 2
        "Content-Type": "application/json",
    }

    # Attempt to PATCH Deal 2 (which belongs to Org 1)
    patch_payload = {"title": "Hacked"}
    resp = requests.patch(f"{BASE_URL}/deals/2", json=patch_payload, headers=spy_headers)

    log("Spy Patch Status:", resp.status_code)
    log("Spy Patch Body:", resp.json())
    if resp.status_code in [403, 404]:
        print("SUCCESS: Cross-tenant access denied.")
    else:
        print(f"FAILURE: Spy was able to access/patch deal. Status: {resp.status_code}")


if __name__ == "__main__":
    test_task_past_due()
    test_won_deal_zero_amount()
    test_delete_contact_with_deals()
    test_cross_tenant_access()
