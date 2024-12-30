from google.cloud.logging import Client
from datetime import datetime


class MissingQueryParameterException(Exception):
    """Custom exception for missing query parameters."""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidFilterQueryException(Exception):
    """Custom exception for invalid filtering query provided."""

    def __init__(self, message: str):
        super().__init__(message)


class CloudLogsQuery:
    def __init__(self, client: Client):
        """
        Initialize the CloudLogsQuery with service account credentials.

        :param client: Injected logging Client.
        """
        self.client = client

    async def query_logs(
        self,
        cloud_function_name: str,
        cloud_function_region: str,
        start_time: datetime,
        end_time: datetime,
        query: str = "",
        severity: str = "DEFAULT",
    ) -> list:
        """
        Query logs for a specified Cloud Function within a given time range.
        :param cloud_function_name: Name of the Cloud Function to query logs for.
        :param query: The string query to filter logs.
        :param start_time: Start of the time range for logs (datetime object).
        :param end_time: End of the time range for logs (datetime object).
        :param severity: (Optional) Minimum severity level for logs (e.g., "ERROR").
        :return: Logs in list structure (nested objects).
        :raises MissingQueryParameterException: If any required parameter is missing.
        """
        if not all([cloud_function_name, cloud_function_region, start_time, end_time]):
            raise MissingQueryParameterException(
                "All parameters (cloud_function_name, cloud_function_region, query, start_time, end_time) must be provided."
            )

        start_time_string = f"{start_time.year}-{start_time.month}-{start_time.day}T{start_time.hour}:{start_time.minute}:{start_time.second}Z"
        end_time_string = f"{end_time.year}-{end_time.month}-{end_time.day}T{end_time.hour}:{end_time.minute}:{end_time.second}Z"

        # Build the log filter
        log_filter = f"""(resource.type = "cloud_function"
            resource.labels.function_name = "{cloud_function_name}"
            resource.labels.region = "{cloud_function_region}")
            OR
            (resource.type = "cloud_run_revision"
            resource.labels.service_name = "{cloud_function_name}"
            resource.labels.location = "{cloud_function_region}")
            timestamp >= "{start_time_string}" AND timestamp <= "{end_time_string}"
            severity = {severity}
            """
        if query:
            log_filter += f"AND {query}"

        try:
            log_entries = self.client.list_entries(filter_=log_filter)
            logs = []
            for entry in log_entries:
                text_payload = None
                if isinstance(entry.payload, dict):
                    text_payload = entry.payload.get("message")
                elif isinstance(entry.payload, str):
                    text_payload = entry.payload
                logs.append(
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "severity": entry.severity,
                        "textPayload": text_payload,
                        "resource": entry.resource.labels,
                    }
                )
            return logs
        except:
            raise InvalidFilterQueryException("Invalid filter query provided.")
