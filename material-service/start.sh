#!/bin/bash

echo "Material Service starting..."
PORT=${PORT:-8004}
echo "Port: $PORT"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" 