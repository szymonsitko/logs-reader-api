#!/bin/bash

export GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH="/home/ssitko/Documents/projects/fastapi/python/sa-credentials.json"
export MYSQL_CONNECTION_STRING="mysql+pymysql://root:password@localhost:3306/logs"

fastapi dev ./main.py