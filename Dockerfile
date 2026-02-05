# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Set environment variables to prevent Python from writing pyc files to disc
# and buffering stdout and stderr.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y gcc build-essential && rm -rf /var/lib/apt/lists/*

# Install dependencies
# We install directly just for this single file app, or we could copy requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn pydantic pyahocorasick

# Copy the application code
COPY safe_med_agent.py .

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "safe_med_agent:app", "--host", "0.0.0.0", "--port", "8000"]
