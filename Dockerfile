# Stage 1: Build frontend
FROM node:18-slim AS frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY frontend/.npmrc ./
RUN npm install

# Copy rest of frontend
COPY frontend/ .

# Build using vite
RUN npm run build

# Stage 2: Python backend and final image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    net-tools \
    procps \
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

# Create necessary directories
RUN mkdir -p uploads downloads logs

# Copy frontend - handle both dev and prod
ARG ENVIRONMENT
ENV ENVIRONMENT=${ENVIRONMENT:-production}

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

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
ENV API_PORT=8000
ENV FRONTEND_PORT=5173

# Update entrypoint script to run both services
ENTRYPOINT ["./entrypoint.sh"]