# Use a base image with AWS Lambda Python support
FROM public.ecr.aws/lambda/python:3.12

# Install required Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY ./ ./service

# Set the FastAPI entry point for Lambda
CMD ["service.main.handler"]
