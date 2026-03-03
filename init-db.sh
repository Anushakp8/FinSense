#!/bin/bash
set -e

# Create the Airflow metadata database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE airflow;
    -- Enable TimescaleDB extension on the main finsense database
    CREATE EXTENSION IF NOT EXISTS timescaledb;
EOSQL
