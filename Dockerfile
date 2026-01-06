# Use an official lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y gcc python3-dev
RUN pip install kafka-python pandas kagglehub

# Copy your script into the container
COPY producer.py .
# We don't copy the DB here because we want it to be created in the volume if it doesn't exist

# Command to run the script
CMD ["python", "-u", "producer.py"]