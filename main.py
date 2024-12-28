from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from google.cloud import logging
from pydantic import BaseModel
from typing import List, Dict, Any

from src.app.repository.log import (
    CloudLogsQuery,
    InvalidFilterQueryException,
    MissingQueryParameterException,
)
from src.pkg.settings import Settings


class LogEntry(BaseModel):
    timestamp: str
    severity: str | None
    textPayload: str | None
    resource: Dict[str, Any]


# Define the FastAPI app wrapper
def api(settings: Settings) -> FastAPI:
    # Get all GCP logs for service
    app = FastAPI()

    @app.get(
        "/logs/{cloud_function_name}",
        response_model=List[LogEntry],
        responses={
            400: {"description": "Missing required parameters."},
            422: {"description": "Invalid filter query provided."},
            500: {"description": "Internal server error."},
        },
    )
    async def get_logs(
        cloud_function_name: str,
        cloud_function_region: str,
        start_time: str,
        end_time: str,
        log_query: str = "",
        severity: str = "DEFAULT",
    ):
        try:
            logging_client = logging.Client.from_service_account_json(
                settings.service_account_credentials
            )
            log_query_client = CloudLogsQuery(logging_client)
            logs: list = log_query_client.query_logs(
                cloud_function_name=cloud_function_name,
                cloud_function_region=cloud_function_region,
                query=log_query,
                start_time=datetime.fromisoformat(start_time),
                end_time=datetime.fromisoformat(end_time),
                severity=severity,
            )
            return logs
        except Exception as e:
            if isinstance(e, MissingQueryParameterException) or isinstance(
                e, ValueError
            ):
                raise HTTPException(status_code=400, detail="Missing required parameters.")
            if isinstance(e, InvalidFilterQueryException):
                raise HTTPException(status_code=422, detail="Invalid filter query provided.")
            raise HTTPException(status_code=500, detail=f"Internal server error: {repr(e)}.")

    return app


# Initialize the FastAPI app
app = api(settings=Settings())
