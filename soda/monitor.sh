#!/bin/bash

echo "Starting Soda Core data quality monitoring..."

# Install required packages
echo "Installing required packages..."
apt-get update -qq && apt-get install -y netcat-openbsd --quiet
pip install soda-core-trino --quiet

# Wait for Trino to be ready  
echo "Waiting for Trino to be available..."
timeout=300
while ! nc -z trino 8080; do
    echo "Trino not ready, waiting 10 seconds..."
    sleep 10
    timeout=$((timeout - 10))
    if [ $timeout -le 0 ]; then
        echo "Timeout waiting for Trino"
        exit 1
    fi
done

echo "Trino is ready. Testing connection..."

# Test connection first
soda test-connection -d trino -c /soda/configuration.yml

if [ $? -ne 0 ]; then
    echo "Connection test failed. Waiting 30 seconds and retrying..."
    sleep 30
    soda test-connection -d trino -c /soda/configuration.yml
fi

echo "Starting data quality checks..."

# Run initial scan
echo "Running initial data quality scan..."
soda scan -d trino -c /soda/configuration.yml /soda/checks.yml

# Run periodic scans every 5 minutes
echo "Starting periodic data quality monitoring (every 5 minutes)..."
while true; do
    sleep 300  # 5 minutes
    echo "$(date): Running scheduled data quality scan..."
    soda scan -d trino -c /soda/configuration.yml /soda/checks.yml
    echo "Scan completed. Next scan in 5 minutes..."
done