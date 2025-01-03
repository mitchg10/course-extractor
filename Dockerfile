# Stage 1: Build frontend
FROM node:18-slim AS frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy .npmrc file
COPY frontend/.npmrc ./

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
# Build using vite
RUN npm run build

# Stage 2: Python backend and final image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install pyvt
COPY pyvt pyvt
RUN pip install pyvt/

# Copy backend code
COPY backend/ backend/
COPY config/ config/

# Create necessary directories
RUN mkdir -p data/individual data/combined logs

# Copy frontend - handle both dev and prod
ARG ENVIRONMENT
ENV ENVIRONMENT=${ENVIRONMENT:-production}

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist frontend/dist

# Create frontend directory for development volume mount
RUN mkdir -p frontend

# Copy entrypoint script
COPY setup/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose ports for FastAPI and React
EXPOSE 8000
EXPOSE 5173

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Update entrypoint script to run both services
ENTRYPOINT ["./entrypoint.sh"]