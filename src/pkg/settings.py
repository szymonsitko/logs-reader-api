from pydantic_settings import BaseSettings

import os

DEFALUT_SERVICE_ACCOUNT_CREDENTIALS_ENV_VAR = "GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH"


class Settings(BaseSettings):
    service_account_credentials: str | None = os.getenv(
        DEFALUT_SERVICE_ACCOUNT_CREDENTIALS_ENV_VAR
    )

    def __init__(self):
        super().__init__()

    def set_service_account_credentials_env_var(
        self, service_account_credentials: str
    ) -> None:
        self.service_account_credentials = service_account_credentials
