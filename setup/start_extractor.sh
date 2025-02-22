#!/bin/bash

# Default to development mode
ENVIRONMENT=${1:-development}
echo "Starting Course Extractor in $ENVIRONMENT mode..."

# Verify the user has docker installed
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running!"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if docker compose is installed
if ! docker compose --version &> /dev/null; then
    echo "Error: Docker Compose is not installed!"
    read -p "Press Enter to exit..."
    exit 1
fi

# Install docker compose if not installed
if ! docker compose --version &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo apt-get install -y docker-compose
fi

# Create basic directories
mkdir -p uploads downloads logs

# Clean up any existing containers
docker compose down

# Start the containers
docker compose up --build -d

# Verify the containers are running
if [ $? -eq 0 ]; then
    echo
    echo "Application started successfully!"
else
    echo
    echo "Error: There was a problem starting the application."
    echo "Please check the logs for more information."
fi

echo "Course Extractor is starting!"
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000"
echo
echo "To view logs: docker compose logs -f"
echo "To stop: docker compose down"

# Show logs
docker compose logs -f