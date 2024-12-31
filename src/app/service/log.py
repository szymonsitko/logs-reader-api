from datetime import datetime

from src.app.repository.domain import CloudLogsInterface, LogEntry


class LogsService:
    def __init__(
        self,
        logs_repository: CloudLogsInterface,
    ):
        self.logs_repository: CloudLogsInterface = logs_repository

    async def get_logs(
        self,
        cloud_function_name: str,
        cloud_function_region: str,
        start_time: datetime,
        end_time: datetime,
        query: str = "",
        severity: str = "DEFAULT",
    ) -> list[LogEntry]:
        logs = await self.logs_repository.query_logs(
            cloud_function_name=cloud_function_name,
            cloud_function_region=cloud_function_region,
            start_time=start_time,
            end_time=end_time,
            query=query,
            severity=severity,
        )
        return logs
