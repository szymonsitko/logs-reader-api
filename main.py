from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from google.cloud import logging

from src.app.repository.log import (
    CloudLogsQuery,
    InvalidFilterQueryException,
    MissingQueryParameterException,
)
from src.pkg.settings import Settings


# Define the FastAPI app wrapper
def api(settings: Settings) -> FastAPI:
    # Get all GCP logs for service
    app = FastAPI()

    @app.get("/logs/{cloud_function_name}")
    async def get_logs(
        cloud_function_name: str,
        cloud_function_region=str,
        start_time=str,
        end_time=str,
        log_query=None,
        severity=None,
    ):
        if log_query is None:
            log_query = ""
        if severity is None:
            severity = "DEFAULT"

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
                return JSONResponse(
                    status_code=400,
                    content={"message": "Missing required parameters."},
                )
            if isinstance(e, InvalidFilterQueryException):
                return JSONResponse(
                    status_code=422,
                    content={"message": "Invalid filter query provided."},
                )
            return JSONResponse(
                status_code=500,
                content={"message": f"Internal server error: {repr(e)}."},
            )

    return app


# Initialize the FastAPI app
if __name__ == "__main__":
    app = api(settings=Settings())
