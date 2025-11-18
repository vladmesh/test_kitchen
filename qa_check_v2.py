import json
import random
import string

import requests

BASE_URL = "http://localhost:8000/api/v1"


def random_string(length=8):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


def log(msg, status="INFO", data=None):
    print(f"[{status}] {msg}")
    if data:
        print(json.dumps(data, indent=2))


def run_tests():
    results = []

    # === SCENARIO 1: Registration & Organization Discovery ===
    email = f"user_{random_string()}@example.com"
    password = "password123"
    org_name = f"Org_{random_string()}"

    log(f"1. Registering user {email}...", "TEST")
    payload = {
        "email": email,
        "password": password,
        "name": "Test User",
        "organization_name": org_name,
    }

    resp = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if resp.status_code in [200, 201]:
        log("Registration successful", "PASS")
        results.append(
            {"id": 1, "desc": "Registration", "status": "PASS", "details": "201 Created"}
        )
        token = resp.json().get("access_token")
    else:
        log(f"Registration failed: {resp.text}", "FAIL")
        results.append({"id": 1, "desc": "Registration", "status": "FAIL", "details": resp.text})
        return results

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Org (Discovery) - SHOULD WORK WITHOUT HEADER NOW
    log("2. Getting Organization info (No Header)...", "TEST")
    resp = requests.get(f"{BASE_URL}/organizations/me", headers=headers)

    org_id = None
    if resp.status_code == 200:
        orgs = resp.json().get("items", [])
        log(f"Got orgs: {len(orgs)} found", "PASS")
        if len(orgs) > 0:
            org_id = orgs[0].get("id")
            results.append(
                {
                    "id": 2,
                    "desc": "Get Organizations (No Header)",
                    "status": "PASS",
                    "details": "Works!",
                }
            )
        else:
            results.append(
                {
                    "id": 2,
                    "desc": "Get Organizations (No Header)",
                    "status": "FAIL",
                    "details": "Empty list",
                }
            )
    else:
        log(f"Get Organizations failed: {resp.status_code} {resp.text}", "FAIL")
        results.append(
            {
                "id": 2,
                "desc": "Get Organizations (No Header)",
                "status": "FAIL",
                "details": resp.text,
            }
        )

    if not org_id:
        results.append(
            {
                "id": 0,
                "desc": "Blocker",
                "status": "FAIL",
                "details": "Cannot proceed without Org ID",
            }
        )
        return results

    headers["X-Organization-Id"] = str(org_id)

    # === SCENARIO 2: Members Management ===
    log("3. Testing Members Management...", "TEST")

    # Create another user to add
    email_2 = f"colleague_{random_string()}@example.com"
    log(f"Registering second user {email_2}...", "INFO")
    payload_2 = {
        "email": email_2,
        "password": "password123",
        "name": "Colleague",
        "organization_name": f"Org_{random_string()}",  # They get their own org initially
    }
    requests.post(f"{BASE_URL}/auth/register", json=payload_2)

    # Add member
    log(f"Adding {email_2} to Org {org_id}...", "TEST")
    add_member_payload = {"email": email_2, "role": "member"}
    resp = requests.post(
        f"{BASE_URL}/organizations/{org_id}/members", json=add_member_payload, headers=headers
    )

    if resp.status_code == 201:
        log("Member added successfully", "PASS")
        results.append(
            {"id": 3, "desc": "Add Member API", "status": "PASS", "details": "201 Created"}
        )
    elif resp.status_code == 404:
        log("Member add endpoint not found", "FAIL")
        results.append(
            {"id": 3, "desc": "Add Member API", "status": "FAIL", "details": "404 Not Found"}
        )
    else:
        log(f"Member add failed: {resp.status_code} {resp.text}", "FAIL")
        results.append({"id": 3, "desc": "Add Member API", "status": "FAIL", "details": resp.text})

    # === SCENARIO 3: Duplicate Organization Name ===
    log("4. Testing Duplicate Org Name...", "TEST")
    dup_payload = {
        "email": f"dup_{random_string()}@test.com",
        "password": "pass",
        "name": "Dup User",
        "organization_name": org_name,  # Use existing name
    }
    resp = requests.post(f"{BASE_URL}/auth/register", json=dup_payload)
    if resp.status_code == 409:
        log("Duplicate Org Name handled correctly", "PASS")
        results.append(
            {"id": 4, "desc": "Duplicate Org Name", "status": "PASS", "details": "409 Conflict"}
        )
    elif resp.status_code == 500:
        log("Duplicate Org Name caused 500", "FAIL")
        results.append(
            {
                "id": 4,
                "desc": "Duplicate Org Name",
                "status": "FAIL",
                "details": "500 Internal Server Error",
            }
        )
    else:
        log(f"Duplicate Org Name unexpected: {resp.status_code}", "FAIL")
        results.append(
            {
                "id": 4,
                "desc": "Duplicate Org Name",
                "status": "FAIL",
                "details": f"{resp.status_code}",
            }
        )

    # === SCENARIO 4: Happy Path (Contacts, Deals) ===
    # (Brief check to ensure we didn't break existing functionality)
    log("5. Regression Test: Create Contact...", "TEST")
    contact_payload = {
        "name": "John Doe",
        "email": f"john_{random_string()}@doe.com",
        "phone": "+123456789",
    }
    resp = requests.post(f"{BASE_URL}/contacts", json=contact_payload, headers=headers)
    if resp.status_code == 201:
        results.append(
            {"id": 5, "desc": "Create Contact", "status": "PASS", "details": "201 Created"}
        )
    else:
        results.append({"id": 5, "desc": "Create Contact", "status": "FAIL", "details": resp.text})

    print("\n\n--- FINAL REPORT DATA ---")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run_tests()
