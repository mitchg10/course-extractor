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
    tesseract-ocr \
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
COPY --from=frontend-builder /app/frontend/build frontend/build

# Create frontend directory for development volume mount
RUN mkdir -p frontend

# Copy setup scripts
COPY setup/setup_ollama.sh .
COPY setup/entrypoint.sh .
RUN chmod +x setup_ollama.sh entrypoint.sh

# Expose ports for FastAPI and React
EXPOSE 8000
EXPOSE 3000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Update entrypoint script to run both services
ENTRYPOINT ["./entrypoint.sh"]