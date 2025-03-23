# Use the official Python 3.10-slim image as the base image
FROM python:3.10-slim

# Set environment variables
ENV WHATSAPP_API_URL=${WHATSAPP_API_URL}
ENV ACCESS_TOKEN=${ACCESS_TOKEN}
ENV PHONE_NUMBER_ID=${PHONE_NUMBER_ID}
ENV URL=${URL}

# Set the working directory inside the container
WORKDIR /app
COPY /app /app

# Copy the requirements.txt file to install dependencies

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r /app/requirements.txt
# Copy the rest of the application code

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run the FastAPI app with Uvicorn  
CMD ["uvicorn", "multimodal-app:app", "--host", "0.0.0.0", "--port", "8000"]