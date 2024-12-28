#!/bin/bash

# Run server and send it to the background
export GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH=/home/ssitko/Documents/projects/fastapi/python/sa-credentials.json

nohup fastapi dev ./main.py &

sleep 5

# Apply GET curl command
curl --location 'localhost:8000/logs/sample-func?cloud_function_region=europe-central2&start_time=2024-12-01T00%3A00%3A00Z&end_time=2024-12-31T00%3A00%3A00Z'

# Kill the server
kill $(lsof -t -i:8000)