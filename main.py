from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from google.cloud import logging

import os

from src.app.repository.log import CloudLogsQuery
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_account_credentials: str | None = os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH")

settings = Settings()
app = FastAPI()

# Get all GCP logs for service
@app.get("/logs/{cloud_function_name}")
async def get_logs(cloud_function_name: str, cloud_function_region = str, start_time = str, end_time = str, log_query = None, severity = None):
    if log_query is None:
        log_query = ""
    if severity is None:
        severity = "DEFAULT"
        
    try:
        logging_client = logging.Client.from_service_account_json(settings.service_account_credentials)
        log_query_client = CloudLogsQuery(logging_client)
        logs: list = log_query_client.query_logs(
            cloud_function_name=cloud_function_name,
            cloud_function_region=cloud_function_region,
            query=log_query,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            severity=severity
        )
        return logs
    except Exception as e:
        print("Error!", e)
        return JSONResponse(
            status_code=400,
            content={"message": "An error occurred while fetching logs."},
        )
