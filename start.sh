#!/bin/bash

echo "Starting Song Master backend..."
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &

echo "Starting Song Master frontend..."
cd frontend && npm run dev