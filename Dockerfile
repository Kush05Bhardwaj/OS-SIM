# Multi-stage optimized Dockerfile for OS-SIM
FROM python:3.12-slim

# Prevent Python from writing .pyc files & enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501

# Install Linux native core monitoring tools needed by bash/ utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    procps \
    coreutils \
    gawk \
    sed \
    grep \
    util-linux \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source tree
COPY . .

# Ensure bash scripts are executable
RUN chmod +x /app/bash/*.sh

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
