from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from datetime import datetime
from google.cloud import logging
from typing import List, Annotated
from sqlmodel import Session, SQLModel, create_engine, select

from src.app.infrastructure.http import LogEntryNotFoundException
from src.app.repository.model import Log
from src.app.repository.log import (
    CloudLogsQuery,
    InvalidFilterQueryException,
    MissingQueryParameterException,
)
from src.app.repository.domain import LogEntry
from src.pkg.settings import Settings

import json


# Define the FastAPI app wrapper
def api_factory(settings: Settings) -> FastAPI:
    mysql_conn_string = settings.get_mysql_connection_string()
    if mysql_conn_string is None:
        raise ValueError("Mysql connection string must be set")

    engine = create_engine(mysql_conn_string)

    def create_db_and_tables():
        SQLModel.metadata.create_all(engine)

    def get_session():
        with Session(engine) as session:
            yield session

    SessionDep = Annotated[Session, Depends(get_session)]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        create_db_and_tables()
        yield

    app = FastAPI(lifespan=lifespan)

    # Get all GCP logs for service
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
        """
        Query logs for a specified Cloud Function within a given time range.

        :param cloud_function_name: Name of the Cloud Function to query logs for.
        :param cloud_function_region: Region of the Cloud Function.
        :param start_time: Start of the time range for logs (ISO 8601 format).
        :param end_time: End of the time range for logs (ISO 8601 format).
        :param log_query: (Optional) The string query to filter logs.
        :param severity: (Optional) Minimum severity level for logs (e.g., "ERROR").
        :return: List of LogEntry objects.
        :raises HTTPException: If any required parameter is missing or the filter query is invalid.
        """
        try:
            logging_client = logging.Client.from_service_account_json(
                settings.service_account_credentials
            )
            log_query_client = CloudLogsQuery(logging_client)
            logs: list[LogEntry] = await log_query_client.query_logs(
                cloud_function_name=cloud_function_name,
                cloud_function_region=cloud_function_region,
                query=log_query,
                start_time=datetime.fromisoformat(start_time),
                end_time=datetime.fromisoformat(end_time),
                severity=severity,
            )
            return [log.get_log_entry() for log in logs]
        except Exception as e:
            if isinstance(e, MissingQueryParameterException) or isinstance(
                e, ValueError
            ):
                raise HTTPException(
                    status_code=400, detail="Missing required parameters."
                )
            if isinstance(e, InvalidFilterQueryException):
                raise HTTPException(
                    status_code=422, detail="Invalid filter query provided."
                )
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {repr(e)}."
            )

    # Store log entry to the database
    @app.post(
        "/log",
        response_model=LogEntry,
        responses={
            400: {"description": "Missing required parameters."},
            500: {"description": "Internal server error."},
        },
    )
    def store_log_query(
        log: LogEntry, session: Annotated[Session, Depends(get_session)]
    ):
        """
        Store a log entry to the database.

        :param log: LogEntry object to be stored.
        :param session: Database session dependency.
        :return: Stored LogEntry object.
        :raises HTTPException: If any required parameter is missing or an internal server error occurs.
        """
        try:
            log_db = Log(
                severity=log.severity,
                textPayload=log.textPayload,
                timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                resource=json.dumps(log.resource),
            )
            session.add(log_db)
            session.commit()
            session.refresh(log_db)
            return log
        except Exception as e:
            if isinstance(e, ValueError):
                raise HTTPException(
                    status_code=400, detail="Missing required parameters."
                )
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {repr(e)}."
            )

    # Obtain log query from the database
    @app.get(
        "/log/{query_param}",
        response_model=LogEntry | list[LogEntry],
        responses={
            400: {"description": "Missing required parameters."},
            404: {
                "description": "Unable to find log entry using `int` param type, value `1"
            },
        },
    )
    async def get_log_query(
        query_param: int | datetime, session: Annotated[Session, Depends(get_session)]
    ):
        """
        Obtain a log query from the database.

        :param query_param: ID or timestamp of the log entry to query.
        :param session: Database session dependency.
        :return: LogEntry object or list of LogEntry objects.
        :raises HTTPException: If the log entry is not found or any required parameter is missing.
        """
        try:
            match query_param:
                case int():
                    query_log = session.get(Log, query_param)
                case datetime():
                    statement = select(Log).where(Log.timestamp == query_param)
                    query_log = session.exec(statement).first()
            if query_log is None:
                raise LogEntryNotFoundException(
                    message=f"Unable to find log entry using `{'id' if type(query_param) == int else 'datetime'}` param type, value `{query_param}`"
                )
            return LogEntry(
                timestamp=query_log.timestamp,
                severity=query_log.severity,
                textPayload=query_log.textPayload,
                resource=json.loads(query_log.resource) if query_log.resource else None,
            )
        except Exception as e:
            if isinstance(e, LogEntryNotFoundException):
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail="Missing required parameters.")

    return app


# Initialize the FastAPI app
app = api_factory(settings=Settings())
