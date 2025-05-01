# Use an official Python runtime
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install SQLite3 and pip
RUN apt-get update && apt-get install -y sqlite3 python3-pip

# Install dependencies
RUN pip install -r requirements.txt

# Create volume for persistent DB storage
VOLUME ["/app/db"]

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
