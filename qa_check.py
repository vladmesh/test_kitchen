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

    email = f"user_{random_string()}@example.com"
    password = "password123"
    org_name = f"Org_{random_string()}"

    # 1. Registration
    log(f"Registering user {email}...")
    payload = {
        "email": email,
        "password": password,
        "name": "Test User",
        "organization_name": org_name,
    }
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=payload)
        if resp.status_code in [200, 201]:
            log("Registration successful", "PASS", resp.json())
            results.append(
                {"id": 1, "desc": "Registration", "status": "PASS", "details": "201 Created"}
            )
        else:
            log(f"Registration failed: {resp.text}", "FAIL")
            results.append(
                {
                    "id": 1,
                    "desc": "Registration",
                    "status": "FAIL",
                    "details": f"{resp.status_code} {resp.text}",
                }
            )
            return results
    except Exception as e:
        log(f"Connection error: {e}", "CRITICAL")
        return results

    # 2. Login
    log("Logging in...")
    login_payload = {"email": email, "password": password}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        log("Login successful", "PASS")
        results.append({"id": 2, "desc": "Login", "status": "PASS", "details": "Token received"})
    else:
        log(f"Login failed: {resp.text}", "FAIL")
        results.append({"id": 2, "desc": "Login", "status": "FAIL", "details": resp.text})
        return results

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Org (Discovery)
    log("Getting Organization info...")
    # Try without header first (to see if it works or gives the error mentioned in previous report)
    resp = requests.get(f"{BASE_URL}/organizations/me", headers=headers)
    org_id = None

    if resp.status_code == 200:
        orgs = resp.json()
        log(f"Got orgs: {orgs}", "PASS")
        if isinstance(orgs, list) and len(orgs) > 0:
            org_id = orgs[0].get("id")
        results.append(
            {
                "id": 3,
                "desc": "Get Organizations (No Header)",
                "status": "PASS",
                "details": "Works without header",
            }
        )
    elif resp.status_code == 400 and "header" in resp.text.lower():
        log("Get Organizations failed due to missing header (Known Issue)", "FAIL")
        results.append(
            {
                "id": 3,
                "desc": "Get Organizations (No Header)",
                "status": "FAIL",
                "details": "Requires X-Organization-Id header but shouldn't",
            }
        )
        # Try to guess Org ID. Since we just registered, if the DB was empty it's 1.
        # If not, we can't easily guess. But usually registration returns the org.
        # Let's check the registration response again?
        # The TZ doesn't specify registration response structure, but let's assume we are blocked if we can't get it.
        # FOR TEST PURPOSE: I'll try ID 1, 2, ... up to 100 to find the one that belongs to me? No, that returns 403/404.
        # Let's try to parse it from registration if possible, but I didn't save it above.
        # Hack: assume it's the latest one? No access to DB directly here easily (though I could use psql).
        # Let's try to cheat and use the DB to find the org ID for this email.
        pass
    else:
        log(f"Get Organizations failed: {resp.status_code} {resp.text}", "FAIL")
        results.append(
            {"id": 3, "desc": "Get Organizations", "status": "FAIL", "details": resp.text}
        )

    # Workaround to get Org ID if API failed
    if not org_id:
        # Attempt to find it via DB if possible, or just guess.
        # Assuming the previous tool call `make migrate` implies we have `psql` access via docker.
        # I will skip this in python and handle it manually if this step fails.
        # For now, let's assume we need it.
        # Actually, let's try sending the request WITH the header if we can guess it.
        # Wait, if I can't get the ID, I can't set the header. Catch-22.
        # Let's hope registration returned it.
        pass

    # If we are blocked here, we can't proceed with multi-tenant checks properly.
    # But let's try to continue with a guessed ID or if step 3 actually passed.

    # RE-Running registration to capture response better
    # (Actually I printed it above).

    if not org_id:
        log("Trying to fetch Org ID from DB via docker...", "INFO")
        import subprocess

        try:
            cmd = f"docker compose -f infra/docker-compose.dev.yml exec -t db psql -U postgres -d mini_crm -c \"SELECT o.id FROM organizations o JOIN organization_members om ON o.id = om.organization_id JOIN users u ON om.user_id = u.id WHERE u.email = '{email}';\""
            # We need to parse the output.
            # Output format:
            #  id
            # ----
            #   1
            # (1 row)
            output = subprocess.check_output(cmd, shell=True).decode()
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip().isdigit():
                    org_id = int(line.strip())
                    break
            log(f"Found Org ID from DB: {org_id}", "INFO")
        except Exception as e:
            log(f"Failed to get Org ID from DB: {e}", "CRITICAL")
            return results

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

    # 4. Create Contact
    log("Creating Contact...")
    contact_payload = {
        "name": "John Doe",
        "email": f"john_{random_string()}@doe.com",
        "phone": "+123456789",
    }
    resp = requests.post(f"{BASE_URL}/contacts", json=contact_payload, headers=headers)
    contact_id = None
    if resp.status_code == 201:
        contact_id = resp.json().get("id")
        log("Contact created", "PASS")
        results.append(
            {"id": 4, "desc": "Create Contact", "status": "PASS", "details": "201 Created"}
        )
    else:
        log(f"Contact creation failed: {resp.text}", "FAIL")
        results.append({"id": 4, "desc": "Create Contact", "status": "FAIL", "details": resp.text})

    # 5. Create Deal
    if contact_id:
        log("Creating Deal...")
        deal_payload = {
            "contact_id": contact_id,
            "title": "Super Deal",
            "amount": 1000.0,
            "currency": "USD",
        }
        resp = requests.post(f"{BASE_URL}/deals", json=deal_payload, headers=headers)
        deal_id = None
        if resp.status_code == 201:
            deal_id = resp.json().get("id")
            log("Deal created", "PASS")
            results.append(
                {"id": 5, "desc": "Create Deal", "status": "PASS", "details": "201 Created"}
            )
        else:
            log(f"Deal creation failed: {resp.text}", "FAIL")
            results.append({"id": 5, "desc": "Create Deal", "status": "FAIL", "details": resp.text})

        # 6. Update Deal (Won)
        if deal_id:
            log("Updating Deal to WON...")
            patch_payload = {"status": "won", "stage": "closed"}
            resp = requests.patch(
                f"{BASE_URL}/deals/{deal_id}", json=patch_payload, headers=headers
            )
            if resp.status_code == 200:
                log("Deal updated", "PASS")
                results.append(
                    {"id": 6, "desc": "Update Deal (WON)", "status": "PASS", "details": "200 OK"}
                )

                # Check Activity
                resp_act = requests.get(f"{BASE_URL}/deals/{deal_id}/activities", headers=headers)
                activities = resp_act.json()
                has_change = any(a.get("type") == "status_changed" for a in activities)
                if has_change:
                    results.append(
                        {
                            "id": 7,
                            "desc": "Activity Creation",
                            "status": "PASS",
                            "details": "Found status_changed",
                        }
                    )
                else:
                    results.append(
                        {
                            "id": 7,
                            "desc": "Activity Creation",
                            "status": "FAIL",
                            "details": "No status_changed activity found",
                        }
                    )
            else:
                log(f"Deal update failed: {resp.text}", "FAIL")
                results.append(
                    {"id": 6, "desc": "Update Deal (WON)", "status": "FAIL", "details": resp.text}
                )

    # 8. Analytics
    log("Checking Analytics...")
    resp = requests.get(f"{BASE_URL}/analytics/deals/summary", headers=headers)
    if resp.status_code == 200:
        results.append(
            {"id": 8, "desc": "Analytics Summary", "status": "PASS", "details": "200 OK"}
        )
    else:
        results.append(
            {"id": 8, "desc": "Analytics Summary", "status": "FAIL", "details": resp.text}
        )

    # 9. Negative Test: Deal with 0 amount -> Won
    if contact_id:
        log("Negative Test: Deal amount 0 -> WON")
        deal_payload_0 = {
            "contact_id": contact_id,
            "title": "Zero Deal",
            "amount": 0,
            "currency": "USD",
        }
        resp = requests.post(f"{BASE_URL}/deals", json=deal_payload_0, headers=headers)
        if resp.status_code == 201:
            d_id_0 = resp.json().get("id")
            resp_patch = requests.patch(
                f"{BASE_URL}/deals/{d_id_0}",
                json={"status": "won", "stage": "closed"},
                headers=headers,
            )
            if resp_patch.status_code == 400:
                results.append(
                    {
                        "id": 9,
                        "desc": "Validate Amount > 0 for WON",
                        "status": "PASS",
                        "details": "Got 400 as expected",
                    }
                )
            else:
                results.append(
                    {
                        "id": 9,
                        "desc": "Validate Amount > 0 for WON",
                        "status": "FAIL",
                        "details": f"Expected 400, got {resp_patch.status_code}",
                    }
                )
        else:
            log("Could not create zero amount deal for testing", "WARN")

    # 10. Negative Test: Past Due Task
    if deal_id:
        log("Negative Test: Task in Past")
        task_payload = {
            "deal_id": deal_id,
            "title": "Past Task",
            "description": "...",
            "due_date": "2000-01-01",
        }
        resp = requests.post(f"{BASE_URL}/tasks", json=task_payload, headers=headers)
        if resp.status_code == 400 or resp.status_code == 422:
            results.append(
                {
                    "id": 10,
                    "desc": "Validate Future Due Date",
                    "status": "PASS",
                    "details": "Got error as expected",
                }
            )
        else:
            results.append(
                {
                    "id": 10,
                    "desc": "Validate Future Due Date",
                    "status": "FAIL",
                    "details": f"Expected error, got {resp.status_code}",
                }
            )

    print("\n\n--- FINAL REPORT DATA ---")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run_tests()
