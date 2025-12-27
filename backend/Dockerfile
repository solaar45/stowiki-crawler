# Multi-stage build for smaller image size
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies in user space
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . /app

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "api.app:app"]