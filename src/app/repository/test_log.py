import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.app.repository.log import CloudLogsQuery, MissingQueryParameterException

@pytest.fixture
def mock_client():
    with patch('app.repository.log.logging.Client') as mock:
        yield mock

def test_query_logs_success(mock_client):
    mock_instance = mock_client.return_value
    mock_entry = MagicMock()
    mock_entry.timestamp = datetime(2023, 10, 1, 12, 0, 0)
    mock_entry.severity = "INFO"
    mock_entry.payload = "Test log entry"
    mock_entry.resource.labels = {"function_name": "test_function"}
    mock_instance.list_entries.return_value = [mock_entry]

    cloud_logs_query = CloudLogsQuery(mock_client)
    start_time = datetime(2023, 10, 1, 0, 0, 0)
    end_time = datetime(2023, 10, 1, 23, 59, 59)
    logs = cloud_logs_query.query_logs(
        cloud_function_name="test_function",
        cloud_function_region="us-central1",
        start_time=start_time,
        end_time=end_time,
        query="",
        severity="DEFAULT"
    )

    assert len(logs) == 1
    assert logs[0]["textPayload"] == "Test log entry"
    assert logs[0]["severity"] == "INFO"
    assert logs[0]["resource"]["function_name"] == "test_function"

def test_query_logs_missing_parameters(mock_client):
    cloud_logs_query = CloudLogsQuery(mock_client)
    start_time = datetime(2023, 10, 1, 0, 0, 0)
    end_time = datetime(2023, 10, 1, 23, 59, 59)

    with pytest.raises(MissingQueryParameterException):
        cloud_logs_query.query_logs(
            cloud_function_name="",
            cloud_function_region="us-central1",
            start_time=start_time,
            end_time=end_time,
            query="",
            severity="DEFAULT"
        )
