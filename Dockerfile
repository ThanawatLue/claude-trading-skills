FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency configuration
COPY pyproject.toml uv.lock ./

# Install project dependencies plus huggingface_hub and gunicorn
RUN uv pip install --system --no-cache-dir \
    huggingface_hub \
    gunicorn \
    ".[screener,thai,technical]"

# Copy all project files
COPY . .

# Create directory for state / SQLite database
RUN mkdir -p /app/state /app/reports

EXPOSE 7860

# Run Flask using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "--chdir", "/app/dashboard", "app:app"]
