from typing import Any, Dict
from datetime import datetime
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: datetime
    severity: str | None
    textPayload: str | None
    resource: Dict[str, Any]

    def get_log_entry(self) -> dict:
        """
        Get the log entry as a dictionary.

        :return: Dictionary representation of the log entry.
        """
        return {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "textPayload": self.textPayload,
            "resource": self.resource,
        }

    def get_timestamp(self) -> datetime:
        """
        Get the timestamp of the log entry.

        :return: Timestamp of the log entry.
        """
        return self.timestamp

    def get_severity(self) -> str | None:
        """
        Get the severity of the log entry.

        :return: Severity of the log entry.
        """
        return self.severity

    def get_text_payload(self) -> str | None:
        """
        Get the text payload of the log entry.

        :return: Text payload of the log entry.
        """
        return self.textPayload

    def get_resource(self) -> Dict[str, Any]:
        """
        Get the resource labels of the log entry.

        :return: Resource labels of the log entry.
        """
        return self.resource
