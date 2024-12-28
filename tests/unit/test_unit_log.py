from typing import Any
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from google.api_core.exceptions import InvalidArgument
from src.app.repository.log import CloudLogsQuery, MissingQueryParameterException

# Mocked log entry for testing
mock_log_entry = MagicMock()
mock_log_entry.timestamp = datetime(2023, 12, 15, 12, 0, 0)
mock_log_entry.severity = "ERROR"
mock_log_entry.payload = {"message": "Test log entry"}
mock_log_entry.resource.labels = {"function_name": "my-function"}

@pytest.fixture
def mock_logging_client():
    with patch("google.cloud.logging.Client") as mock_client:
        yield mock_client

@pytest.fixture
def cloud_logs_query(mock_logging_client):
    mock_instance = mock_logging_client.return_value
    mock_instance.list_entries.return_value = [mock_log_entry]
    return CloudLogsQuery(mock_instance)

def test_query_logs_success(cloud_logs_query):
    # Act
    results = cloud_logs_query.query_logs(
        cloud_function_name="my-function",
        cloud_function_region="mock-region",
        query="SOMEQUERY",
        start_time=datetime(2023, 12, 1, 0, 0),
        end_time=datetime(2023, 12, 25, 23, 59),
        severity="ERROR"
    )

    # Assert
    assert len(results) == 1
    assert results[0]["severity"] == "ERROR"
    assert results[0]["textPayload"] == "Test log entry"

def test_query_logs_missing_parameters(cloud_logs_query):
    with pytest.raises(MissingQueryParameterException):
        cloud_logs_query.query_logs(
            cloud_function_name="",
            cloud_function_region="",
            query="",
            start_time=None,
            end_time=None
        )

def test_query_logs_invalid_filter(cloud_logs_query, mock_logging_client):
    # Arrange
    mock_instance = mock_logging_client.return_value
    mock_instance.list_entries.side_effect = InvalidArgument("400 Unparseable filter")

    # Act & Assert
    with pytest.raises(InvalidArgument):
        cloud_logs_query.query_logs(
            cloud_function_name="my-function",
            cloud_function_region="mock-region",
            query="INVALIDQUERY",
            start_time=datetime(2023, 12, 1, 0, 0),
            end_time=datetime(2023, 12, 25, 23, 59),
            severity="ERROR"
        )

def test_query_logs_with_severity(cloud_logs_query):
    # Act
    results = cloud_logs_query.query_logs(
        cloud_function_name="my-function",
        cloud_function_region="mock-region",
        query="",
        start_time=datetime(2023, 12, 1, 0, 0),
        end_time=datetime(2023, 12, 25, 23, 59),
        severity="INFO"
    )

    # Assert
    assert len(results) == 1
    assert results[0]["severity"] == "ERROR"

def test_query_logs_without_severity(cloud_logs_query):
    # Act
    results = cloud_logs_query.query_logs(
        cloud_function_name="my-function",
        cloud_function_region="mock-region",
        query="",
        start_time=datetime(2023, 12, 1, 0, 0),
        end_time=datetime(2023, 12, 25, 23, 59)
    )

    # Assert
    assert len(results) == 1
    assert results[0]["severity"] == "ERROR"