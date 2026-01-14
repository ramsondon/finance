# syntax=docker/dockerfile:1

# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /build
COPY frontend ./frontend
WORKDIR /build/frontend
RUN npm install
# Build into /build/static instead of relative path
RUN mkdir -p /build/static
RUN npx tailwindcss -i ./src/index.css -o /build/static/tailwind.css --minify
RUN npx esbuild src/index.jsx --bundle --outfile=/build/static/app.js --minify --sourcemap --loader:.jsx=jsx --loader:.js=jsx --jsx=automatic --jsx-import-source=react
# Verify build
RUN ls -lh /build/static/

# Stage 2: Python application
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy backend code
COPY backend /app/backend

# Copy built frontend from frontend-builder stage
RUN mkdir -p /app/backend/finance_project/static
COPY --from=frontend-builder /build/static/* /app/backend/finance_project/static/

# Verify files were copied
RUN echo "Static files after copy:" && ls -lah /app/backend/finance_project/static/

# Set working directory to where manage.py is
WORKDIR /app/backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=finance_project.settings

# Expose port
EXPOSE 8000

# Default command (overridden in compose)
CMD ["bash", "-lc", "python manage.py migrate && gunicorn finance_project.wsgi:application -b 0.0.0.0:8000"]
