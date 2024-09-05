FROM airbyte/python-connector-base:1.2.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential 

WORKDIR /airbyte/integration_code
COPY . .

# Install Poetry
RUN pip install poetry

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Set the entrypoint
ENV AIRBYTE_ENTRYPOINT="python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]