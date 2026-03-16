FROM python:3.12-slim

# Create and activate a virtualenv inside the container
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

RUN python -m venv $VIRTUAL_ENV

# Install dependencies into the venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (config.json excluded via .dockerignore — mounted at runtime)
COPY src/ src/

# Logs directory — bind-mounted from the host at runtime
RUN mkdir -p logs

CMD ["python", "src/main.py"]
