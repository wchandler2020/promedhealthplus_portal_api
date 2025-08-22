# Use the official Python image as the base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for the database connector
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your Django app runs on (e.g., 8000)
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]