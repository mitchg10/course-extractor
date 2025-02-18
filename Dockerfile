# Stage 1: Build frontend
FROM node:18-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY frontend/.npmrc ./
RUN npm install

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Python backend and final image
FROM python:3.11-slim

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

# Copy frontend build and assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
RUN chmod -R 755 /app/frontend/dist

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENVIRONMENT=production
ENV STATIC_DIR=/app/frontend/dist

# Expose port (Render will use PORT env variable)
EXPOSE 8000

# Start FastAPI server
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT