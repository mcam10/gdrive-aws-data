FROM python:3.9-slim
LABEL org.opencontainers.image.source https://github.com/$OWNER/$REPO

# Set the working directory
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get upgrade && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install required Python libraries
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script to the working directory
COPY gdrive_sync_to_s3.py /app

CMD ["./gdrive_sync_to_s3.py"]

# Set the entrypoint to run the Python script
ENTRYPOINT ["python"]

