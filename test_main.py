from fastapi.testclient import TestClient

import pytest

from main import api
from src.pkg.settings import Settings


@pytest.fixture
def get_app_with_valid_config() -> TestClient:
    app = api(settings=Settings())
    return TestClient(app)


@pytest.fixture
def get_app_with_invalid_config() -> TestClient:
    settings = Settings()
    settings.set_service_account_credentials_env_var("INVALID_CREDENTIALS_ENV_VAR")
    app = api(settings=settings)
    return TestClient(app)


def test_query_logs_success(get_app_with_valid_config):
    response = get_app_with_valid_config.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "europe-central2",
            "start_time": "2024-12-01T00:00:00Z",
            "end_time": "2024-12-31T00:00:00Z",
        },
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


def test_query_logs_missing_parameters(get_app_with_valid_config):
    response = get_app_with_valid_config.get(
        "/logs/sample-func",
        params={"cloud_function_region": "", "start_time": "", "end_time": ""},
    )
    assert response.status_code == 400  # Bad Request


def test_query_logs_invalid_time_format(get_app_with_valid_config):
    response = get_app_with_valid_config.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "europe-central2",
            "start_time": "invalid-time-format",
            "end_time": "2024-12-31T00:00:00Z",
        },
    )
    assert response.status_code == 400  # Bad Request


def test_query_logs_invalid_severity_provided(get_app_with_valid_config):
    response = get_app_with_valid_config.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "europe-central2",
            "start_time": "2024-12-01T00:00:00Z",
            "end_time": "2024-12-31T00:00:00Z",
            "severity": "INVALID",
        },
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_internal_server_error(get_app_with_invalid_config):
    response = get_app_with_invalid_config.get(
        "/logs/sample-func",
        params={
            "cloud_function_region": "europe-central2",
            "start_time": "2024-12-01T00:00:00Z",
            "end_time": "2024-12-31T00:00:00Z",
        },
    )
    assert response.status_code == 500  # Internal Server Error
