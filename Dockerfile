FROM python:3.13-slim-bullseye
ENV PYTHONUNBUFFERED=1

# Install required system utilities
RUN apt-get update && apt-get install -y \
    iputils-ping \
    procps && \ 
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt

# CMD ["tail", "-f", "/dev/null"]
CMD ["python", "src/main.py"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD pgrep -f "python src/main.py" >/dev/null || exit 1
