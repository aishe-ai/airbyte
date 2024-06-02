FROM airbyte/python-connector-base:1.1.0

# install psycopg2 dependencies
RUN apt update
RUN apt install build-essential -y
RUN apt install gcc -y
RUN apt install libpq-dev -y
RUN apt install postgresql postgresql-contrib -y

COPY . ./airbyte/integration_code
RUN pip install ./airbyte/integration_code
RUN pip install -r ./airbyte/integration_code/requirements.txt


# The entrypoint and default env vars are already set in the base image
ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]