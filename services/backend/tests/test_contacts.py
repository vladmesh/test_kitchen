from fastapi.testclient import TestClient

from mini_crm.app.main import app

HEADERS = {"Authorization": "Bearer test", "X-Organization-Id": "1"}


def test_contact_crud_flow() -> None:
    client = TestClient(app)

    create_payload = {"name": "John", "email": "john@example.com", "phone": "+111111"}
    create_response = client.post("/api/v1/contacts", json=create_payload, headers=HEADERS)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == "John"

    list_response = client.get("/api/v1/contacts", headers=HEADERS)
    assert list_response.status_code == 200
    assert list_response.json()["meta"]["total"] >= 1
