from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from datetime import datetime
from google.cloud import logging
from typing import List, Annotated
from sqlmodel import Session, SQLModel, create_engine

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
        try:
            logging_client = logging.Client.from_service_account_json(
                settings.service_account_credentials
            )
            log_query_client = CloudLogsQuery(logging_client)
            logs: list = await log_query_client.query_logs(
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
    def store_log(log: LogEntry, session: Annotated[Session, Depends(get_session)]):
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

    return app


# Initialize the FastAPI app
app = api_factory(settings=Settings())
