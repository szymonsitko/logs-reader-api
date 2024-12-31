from pydantic_settings import BaseSettings

import os

DEFALUT_SERVICE_ACCOUNT_CREDENTIALS_ENV_VAR = "GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH"
MYSQL_CONNECTION_STRING_ENV_VAR = "MYSQL_CONNECTION_STRING"

class Settings(BaseSettings):
    service_account_credentials: str | None = os.getenv(
        DEFALUT_SERVICE_ACCOUNT_CREDENTIALS_ENV_VAR
    )
    mysql_connection_string: str | None = os.getenv(
        MYSQL_CONNECTION_STRING_ENV_VAR
    )

    def __init__(self):
        super().__init__()

    def set_service_account_credentials_env_var(
        self, service_account_credentials_var: str
    ) -> None:
        self.service_account_credentials = os.getenv(service_account_credentials_var)
        
    def set_mysql_connection_string(self, mysql_connection_string: str) -> None:
        self.mysql_connection_string = mysql_connection_string

    def get_service_account_credentialsr(self) -> str | None:
        return self.service_account_credentials
    
    def get_mysql_connection_string(self) -> str | None:
        return self.mysql_connection_string
 