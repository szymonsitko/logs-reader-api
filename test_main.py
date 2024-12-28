from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_query_logs_success():
    response = client.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "europe-central2",
            "start_time": "2024-12-01T00:00:00Z",
            "end_time": "2024-12-31T00:00:00Z"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for log in data:
        assert "timestamp" in log
        assert "severity" in log
        assert "textPayload" in log
        assert "resource" in log
        assert "project_id" in log["resource"]
        assert "configuration_name" in log["resource"]
        assert "service_name" in log["resource"]
        assert "location" in log["resource"]
        assert "revision_name" in log["resource"]

def test_query_logs_missing_parameters():
    response = client.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "",
            "start_time": "",
            "end_time": ""
        }
    )
    assert response.status_code == 400  # Bad Request

def test_query_logs_invalid_time_format():
    response = client.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "europe-central2",
            "start_time": "invalid-time-format",
            "end_time": "2024-12-31T00:00:00Z"
        }
    )
    assert response.status_code == 400  # Bad Request
