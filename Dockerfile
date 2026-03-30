FROM python:3.13-slim

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PIP_BREAK_SYSTEM_PACKAGES=1

WORKDIR /app

COPY ./pyproject.toml ./
RUN pip install --no-cache-dir '.[zeroconf]'
COPY ./ ./

EXPOSE 10500

ENTRYPOINT ["python3", "-m", "default_agent", "--uri", "tcp://0.0.0.0:10500"]
