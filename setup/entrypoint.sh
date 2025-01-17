#!/bin/bash
set -e

# Create required directories if they don't exist
mkdir -p /app/downloads
mkdir -p /app/uploads
mkdir -p /app/logs

# Function to handle process cleanup
cleanup() {
    echo "Shutting down processes..."
    jobs -p | xargs -r kill
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGTERM SIGINT

if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting in development mode..."
    # Start FastAPI with hot reload - FIXED PATH
    uvicorn backend.app.main:app --host 0.0.0.0 --port $API_PORT --reload &
    FASTAPI_PID=$!
    
    # Rest of the development mode setup...
    cd frontend
    if [ -f "package.json" ]; then
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        echo "Starting Vite development server..."
        npm run dev  -- --host 0.0.0.0 --port $FRONTEND_PORT&
        VITE_PID=$!
    else
        echo "Error: Frontend package.json not found in mounted volume"
        exit 1
    fi
    cd ..
else
    echo "Starting in production mode..."
    # Start FastAPI without hot reload - FIXED PATH
    uvicorn backend.app.main:app --host 0.0.0.0 --port $API_PORT &
    FASTAPI_PID=$!
    
    # Rest of the production mode setup...
    if [ -d "frontend/dist" ]; then
        if ! command -v serve &> /dev/null; then
            npm install -g serve
        fi
        echo "Starting production server for Vite build..."
        npx serve -s frontend/dist -l $FRONTEND_PORT &
        VITE_PID=$!
    else
        echo "Error: Frontend dist files not found"
        exit 1
    fi
fi

# Keep the script running and monitor child processes
while true; do
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        echo "FastAPI process died"
        cleanup
    fi
    if ! kill -0 $VITE_PID 2>/dev/null; then
        echo "Vite process died"
        cleanup
    fi
    sleep 1
done