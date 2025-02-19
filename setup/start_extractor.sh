#!/bin/bash

# Print header
echo "Course Data Extractor Launcher"
echo "============================"
echo

# Check if environment argument is provided
ENVIRONMENT=${1:-development}  # Default to development if no arg provided

echo "Running in $ENVIRONMENT mode"
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

# Create required directories if they don't exist
mkdir -p uploads downloads logs

# Set environment variables
export ENVIRONMENT=$ENVIRONMENT
export FRONTEND_PORT=5173
export API_PORT=8000

# Clean up any existing containers
echo "Cleaning up existing containers..."
docker compose down

# Pull and start the containers with environment variable
echo "Building and starting Course Extractor..."
docker compose up --build -d

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 10

# Check if the application is running
if docker compose ps | grep -q "course-extractor"; then
    echo "Course Extractor is running!"
    if [ "$ENVIRONMENT" = "development" ]; then
        echo "Frontend: http://localhost:5173"
    else
        echo "Application: http://localhost:8000"
    fi
    echo "Backend API: http://localhost:8000"
else
    echo "Error: Course Extractor failed to start"
    docker compose logs
    exit 1
fi

# Open the browser (platform-independent)
if [ "$ENVIRONMENT" = "development" ]; then
    URL="http://localhost:5173"
else
    URL="http://localhost:8000"
fi

# Open browser based on operating system
case "$(uname -s)" in
    Darwin*)    open "$URL" ;;             # macOS
    MINGW*)     start "$URL" ;;            # Git Bash on Windows
    MSYS*)      start "$URL" ;;            # MSYS on Windows
    CYGWIN*)    cygstart "$URL" ;;         # Cygwin on Windows
    *)          xdg-open "$URL" ;;         # Linux
esac

echo
echo "Application is running!"
echo "You can access it at: $URL"
echo
echo "To stop the application, run: ./stop_extractor.sh"
echo "To view logs, run: docker compose logs -f"
echo

# Keep container running and show logs
docker compose logs -f