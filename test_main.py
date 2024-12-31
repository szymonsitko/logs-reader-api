from fastapi.testclient import TestClient
from datetime import datetime
from main import api_factory
from src.pkg.settings import Settings
from src.app.repository.model import Log
from sqlmodel import Session, create_engine, SQLModel

from src.app.infrastructure.config import ServiceAccountFileNotFouncError

import pytest
import random
import os


@pytest.fixture
def random_log_entry_id() -> int:
    return random.randint(10, 999)


@pytest.fixture
def get_app_with_valid_config() -> TestClient:
    app = api_factory(settings=Settings())
    return TestClient(app)


@pytest.fixture
def get_app_with_invalid_config() -> TestClient:
    invalid_service_account_json_path_env_key = "INVALID_CREDENTIALS_ENV_PATH_VAR"
    os.environ[invalid_service_account_json_path_env_key] = "/user/invalid/path.json"
    settings = Settings()
    settings.set_service_account_credentials_env_var(
        invalid_service_account_json_path_env_key
    )
    app = api_factory(settings=settings)
    return TestClient(app)


@pytest.fixture
def setup_database(random_log_entry_id):
    settings = Settings()
    mysql_conn_string = settings.get_mysql_connection_string()
    engine = create_engine(mysql_conn_string)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        log_entry = Log(
            id=random_log_entry_id,
            severity="ERROR",
            textPayload="Test log entry",
            timestamp=datetime(2023, 12, 15, 12, 0, 0).strftime("%Y-%m-%d %H:%M:%S"),
            resource='{"project_id": "test", "configuration_name": "test", "service_name": "test", "location": "test", "revision_name": "test"}',
        )
        session.add(log_entry)
        session.commit()
        yield
        session.delete(log_entry)
        session.commit()


# Valid app config tests
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


def test_internal_server_error_store_log_invalid_datetime(get_app_with_valid_config):
    response = get_app_with_valid_config.post(
        "/log",
        json={
            "severity": "ERROR",
            "textPayload": "Test log entry",
            "timestamp": "invalid-time-format",
            "resource": {
                "project_id": "test",
                "configuration_name": "test",
                "service_name": "test",
                "location": "test",
                "revision_name": "test",
            },
        },
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_get_log_query_success(
    get_app_with_valid_config, setup_database, random_log_entry_id
):
    response = get_app_with_valid_config.get(f"/log/{random_log_entry_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "ERROR"
    assert data["textPayload"] == "Test log entry"
    assert data["timestamp"] == "2023-12-15T12:00:00"
    assert data["resource"]["project_id"] == "test"


def test_get_log_query_not_found(get_app_with_valid_config):
    response = get_app_with_valid_config.get("/log/999")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Unable to find log entry using `id` param type, value `999`"
    }


# Invalid app config (sevice account json) tests
def test_internal_server_error_invalid_settings(get_app_with_invalid_config):
    try:
        get_app_with_invalid_config.get(
            "/logs/sample-func",
            params={
                "cloud_function_region": "europe-central2",
                "start_time": "2024-12-01T00:00:00Z",
                "end_time": "2024-12-31T00:00:00Z",
            },
        )
    except Exception as e:
        assert isinstance(e, ServiceAccountFileNotFouncError)
