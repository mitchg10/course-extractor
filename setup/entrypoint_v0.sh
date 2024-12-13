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

# Check if we're in development or production
if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting in development mode..."
    # Start FastAPI with hot reload
    uvicorn backend.app:app --host 0.0.0.0 --port $PORT --reload &
    # Start React development server
    # cd frontend && npm start &
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
    else
        echo "Error: Frontend package.json not found in mounted volume"
        exit 1
    fi
    cd ..
else
    echo "Starting in production mode..."
    # Start FastAPI without hot reload
    uvicorn backend.app:app --host 0.0.0.0 --port $PORT &
    # Serve React build
    # npx serve -s frontend/build -l 3000 &
    # Serve React build
    if [ -d "frontend/build" ]; then
        npx serve -s frontend/build -l 3000 &
    else
        echo "Error: Frontend build files not found"
        exit 1
    fi
fi

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?