# Use official Python 3.11 image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# # Collect static files (optional, adjust if you handle static differently)
# RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Run the app with Gunicorn
CMD ["gunicorn", "promed_backend_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
