# 1. Base image
FROM python:bullseye

# 2. Copy files
COPY . /src

# 3. Install dependencies
RUN apt-get update && apt-get install -y iputils-ping
RUN pip install .

ENV PYTHONPATH /src
WORKDIR /src

ENTRYPOINT [ "watchtower-server" ]