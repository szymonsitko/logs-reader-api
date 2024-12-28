from pydantic_settings import BaseSettings

import os

class Settings(BaseSettings):
    service_account_credentials: str | None = os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH")

