# Stage 1: Build frontend
FROM node:18-slim AS frontend-builder
WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json frontend/.npmrc ./
RUN npm install
COPY frontend/ .

# In development, we only need node_modules
# In production, we build the static files
ARG ENVIRONMENT=development
RUN if [ "$ENVIRONMENT" = "production" ]; then \
        npm run build; \
    fi

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    npm \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment and paths
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Create storage directories
RUN mkdir -p uploads downloads logs frontend/dist

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install pyvt
COPY pyvt pyvt
RUN pip install pyvt/

# Copy backend code
COPY backend/ backend/

# Copy frontend files
COPY --from=frontend-builder /app/frontend /app/frontend
RUN chmod -R 755 /app/frontend

# Expose standard ports
EXPOSE 8000 5173

# Start the application
CMD if [ "$ENVIRONMENT" = "production" ]; then \
        uvicorn backend.app.main:app --host 0.0.0.0 --port 8000; \
    else \
        cd /app/frontend && npm run dev -- --host 0.0.0.0 --port 5173 & \
        uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload; \
    fi