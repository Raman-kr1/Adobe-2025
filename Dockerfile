# Specify the base image with the correct platform [cite: 2]
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages [cite: 3]
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Python script and any other necessary files into the container
COPY process_pdfs.py .

# Command to run the script when the container starts
CMD ["python", "process_pdfs.py"]