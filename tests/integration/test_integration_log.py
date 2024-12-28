import os
import pytest

from datetime import datetime
from google.cloud import logging

from src.app.repository.log import CloudLogsQuery


@pytest.fixture
def cloud_logs_query() -> CloudLogsQuery:
    sa_credentials = os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH")
    if sa_credentials is None:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH environment variable is not set."
        )
    logging_client = logging.Client.from_service_account_json(sa_credentials)
    return CloudLogsQuery(logging_client)


@pytest.fixture
def get_function_name() -> str | None:
    return os.environ.get("FUNCTION_NAME")


def test_query_logs_success(cloud_logs_query: CloudLogsQuery, get_function_name: str):
    # Queries
    queries = {"ERROR": "POST"}

    # Arrange
    cloud_function_region = "europe-central2"
    start_time = datetime(2024, 12, 1, 0, 0).astimezone()
    end_time = datetime(2024, 12, 31, 0, 0).astimezone()
    function_name = get_function_name

    # Act
    for test_query in queries.items():
        log_severity, query = test_query
        result = cloud_logs_query.query_logs(
            cloud_function_name=function_name,
            cloud_function_region=cloud_function_region,
            query=query,
            start_time=start_time,
            end_time=end_time,
            severity=log_severity,
        )

        # Assert
        assert len(result) > 0
        for entry in result:
            entry_timestamp = datetime.fromisoformat(entry["timestamp"]).astimezone()
            assert entry_timestamp >= start_time
            assert entry_timestamp <= end_time
            assert entry["severity"] == log_severity
