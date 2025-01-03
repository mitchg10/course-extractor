#!/bin/bash
set -e

# Create required directories if they don't exist
mkdir -p /app/data/individual
mkdir -p /app/data/combined
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
    # Start FastAPI with hot reload
    uvicorn backend.app:app --host 0.0.0.0 --port $PORT --reload &
    FASTAPI_PID=$!
    
    # Handle frontend in development mode
    cd frontend
    if [ -f "package.json" ]; then
        # Install dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi
        echo "Starting Vite development server..."
        npm run dev &
        VITE_PID=$!
    else
        echo "Error: Frontend package.json not found in mounted volume"
        exit 1
    fi
    cd ..
else
    echo "Starting in production mode..."
    # Start FastAPI without hot reload
    uvicorn backend.app:app --host 0.0.0.0 --port $PORT &
    FASTAPI_PID=$!
    
    # Serve Vite build using a static file server
    if [ -d "frontend/dist" ]; then
        # Install serve if not already installed
        if ! command -v serve &> /dev/null; then
            npm install -g serve
        fi
        echo "Starting production server for Vite build..."
        npx serve -s frontend/dist -l 5173 &
        VITE_PID=$!
    else
        echo "Error: Frontend dist files not found"
        exit 1
    fi
fi

# Keep the script running and monitor child processes
while true; do
    # Check if either process has exited
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