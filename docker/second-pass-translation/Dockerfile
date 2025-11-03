FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY docker/second-pass-translation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities
COPY shared/ /app/shared/

# Copy stage script
COPY docker/second-pass-translation/second_pass_translation.py /app/

# Set entrypoint
ENTRYPOINT ["python", "/app/second_pass_translation.py"]
