#!/bin/bash

# Valiate user input
if [ -z "$1" ]; then
    echo -n "Enter testing mode (integration|unit|api|all): " 
    read testing_mode
else
    testing_mode=$1
fi

# Export variables
export PROJECT_ID=k8s-deployment
export FUNCTION_NAME=sample-func
export GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_PATH=/home/ssitko/Documents/projects/fastapi/python/sa-credentials.json

# Run tests
if [ "$testing_mode" == "integration" ]; then
    python -m pytest './tests/integration/.'
elif [ "$testing_mode" == "unit" ]; then
    python -m pytest './tests/unit/.'
elif [ "$testing_mode" == "api" ]; then
    echo ">>> Warning! App must be running at least on localhost:8000!"

    python -m pytest ./test_main.py
elif [ "$testing_mode" == "all" ]; then
     python -m pytest './tests/unit/.'
    python -m pytest './tests/integration/.'

    echo ">>> Warning! App must be running at least on localhost:8000!"

    python -m pytest ./test_main.py
else
    echo "Invalid testing mode. Please enter either 'integration', 'unit' or 'api'"
    exit 1
fi
