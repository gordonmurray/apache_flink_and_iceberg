#!/bin/bash

# Install Trino connector for Superset
pip install trino[sqlalchemy] pyhive[trino]

# Initialize Superset database
superset db upgrade

# Create admin user
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin

# Initialize Superset roles and permissions
superset init

# Start Superset
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger