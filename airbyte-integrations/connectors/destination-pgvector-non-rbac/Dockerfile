FROM airbyte/python-connector-base:1.1.0

COPY . ./airbyte/integration_code
RUN pip install ./airbyte/integration_code
RUN pip install -r ./airbyte/integration_code/requirements.txt

# The entrypoint and default env vars are already set in the base image
ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]