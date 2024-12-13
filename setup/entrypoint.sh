#!/bin/bash
set -e

# Create required directories if they don't exist
mkdir -p /app/data/individual
mkdir -p /app/data/combined
mkdir -p /app/logs

# Run Ollama setup script
echo "Setting up Ollama..."
./setup_ollama.sh

# Wait for Ollama setup to complete
echo "Waiting for Ollama setup to complete..."
timeout=120  # 2 minutes timeout
elapsed=0
until curl -s http://${OLLAMA_HOST}:11434/api/tags > /dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "Timeout waiting for Ollama setup"
        exit 1
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "Still waiting for Ollama setup... ($elapsed seconds elapsed)"
done

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
        echo "Starting frontend development server..."
        npm start &
        REACT_PID=$!
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
    
    # Serve React build
    if [ -d "frontend/build" ]; then
        npx serve -s frontend/build -l 3000 &
        REACT_PID=$!
    else
        echo "Error: Frontend build files not found"
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
    if ! kill -0 $REACT_PID 2>/dev/null; then
        echo "React process died"
        cleanup
    fi
    sleep 1
done