# Stage 1: Build frontend
FROM node:18-slim AS frontend-builder

# Add build argument for environment
ARG ENVIRONMENT=production
ENV NODE_ENV=${ENVIRONMENT}

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY frontend/.npmrc ./
RUN npm install

# Copy frontend source
COPY frontend/ .

# Always create dist directory and build in production
RUN mkdir -p dist && \
    if [ "$ENVIRONMENT" = "production" ] ; then \
        npm run build ; \
    else \
        echo "Development mode - skipping production build" ; \
    fi

# Stage 2: Python backend and final image
FROM python:3.11-slim

# Add build argument for environment
ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    npm \
    net-tools \
    procps \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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
RUN mkdir -p uploads downloads logs frontend/dist

# Always copy frontend files needed for both environments
COPY --from=frontend-builder /app/frontend /app/frontend
RUN chmod -R 755 /app/frontend

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV STATIC_DIR=/app/frontend/dist
ENV VITE_API_URL=http://localhost:8000

# Expose ports
EXPOSE 8000
EXPOSE 5173

# Start command based on environment
CMD if [ "$ENVIRONMENT" = "production" ] ; then \
        uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT ; \
    else \
        cd /app/frontend && npm run dev & \
        uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --reload ; \
    fi