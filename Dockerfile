FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 jira-mcp && chown -R jira-mcp:jira-mcp /app
USER jira-mcp

# Expose ports for HTTP mode
EXPOSE 8000

# Use ENTRYPOINT to allow arguments
ENTRYPOINT ["python", "main.py"]

# Default arguments (can be overridden)
CMD []
