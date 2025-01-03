#!/bin/bash

# Print header
echo "Course Data Extractor Launcher"
echo "============================"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed! Please install Docker Desktop first."
    echo "You can download it from: https://www.docker.com/products/docker-desktop"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Docker is not running! Please start Docker Desktop."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Starting Course Data Extractor..."
echo "This may take a few minutes on first run..."
echo

# Create required directories if they don't exist
mkdir -p data/individual
mkdir -p data/combined
mkdir -p logs

# Pull and start the containers
echo "Building and starting Course Extractor..."
docker compose up --build -d

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 5

# Check if the application is running
if docker compose ps | grep -q "course-extractor"; then
    echo "Course Extractor is running!"
    echo "Backend API: http://localhost:8000"
    echo "Frontend: http://localhost:5173"
else
    echo "Error: Course Extractor failed to start"
    docker-compose logs
    exit 1
fi

# Open the browser (works on macOS)
open http://localhost:5173

echo
echo "Application is running!"
echo "You can access it at: http://localhost:5173"
echo
echo "To stop the application, close this window and run stop_extractor.sh"
echo

# Make sure the script doesn't exit immediately
read -p "Press Enter to exit..."