#!/bin/bash

echo "Stopping Course Data Extractor..."

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running!"
    read -p "Press Enter to exit..."
    exit 1
fi

# Stop the containers
docker compose down

# Verify all containers are stopped
if [ $? -eq 0 ]; then
    echo
    echo "Application stopped successfully!"
else
    echo
    echo "Error: There was a problem stopping the application."
    echo "Please check if any containers are still running with: docker ps"
fi

echo
read -p "Press Enter to exit..."