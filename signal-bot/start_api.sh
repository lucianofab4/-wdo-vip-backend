#!/bin/bash
set -e
if [ -f /opt/venv/bin/activate ]; then
    . /opt/venv/bin/activate
fi
exec uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
