FROM bitnami/spark:3.5.0

USER root
RUN apt-get update && apt-get install -y curl

USER 1001

WORKDIR /app

COPY . .
