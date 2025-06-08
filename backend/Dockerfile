# Stage 1: Base image
FROM python:3.12-slim

# Set environment variables to prevent bytecode files and to run in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Install build-essential for packages that need to be compiled, and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code into the container
COPY ./app /app/app

# The command to run the specific service (api or worker) will be provided in docker-compose.yml
# This makes the image reusable for different roles.
EXPOSE 8000 