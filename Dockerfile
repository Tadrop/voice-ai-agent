FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY execution ./execution
COPY directives ./directives

EXPOSE 8000
CMD ["uvicorn", "execution.twilio_websocket_server:app", "--host", "0.0.0.0", "--port", "8000"]
