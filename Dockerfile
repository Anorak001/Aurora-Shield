# Aurora Shield - INFOTHON 5.0 Docker Image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose the dashboard port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/dashboard/stats || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV AURORA_ENV=docker
ENV FLASK_ENV=production

# Create non-root user for security and add to docker group
RUN useradd -m -u 1000 aurora && \
    groupadd -f docker && \
    usermod -aG docker aurora && \
    chown -R aurora:aurora /app

# Don't switch to aurora user yet - stay as root for Docker access
# USER aurora

# Start the application
CMD ["python", "main.py"]