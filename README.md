# Apache Flink + Iceberg + MinIO CDC Pipeline

A data pipeline demonstrating Change Data Capture (CDC) from MariaDB to Apache Iceberg tables stored in MinIO (S3-compatible storage).

## Architecture

- **Apache Flink 1.19.3** - Stream processing framework
- **Apache Iceberg 1.6.1** - Modern data lake table format
- **MinIO** - S3-compatible object storage
- **MariaDB 10.6.14** - Source database with sample data
- **MySQL CDC 3.1.0** - Change data capture connector

## Features

- Real-time CDC from MariaDB to Iceberg tables
- Parquet file format with Iceberg metadata
- Self-contained with MinIO
- Docker Compose orchestration
- Custom Flink image with embedded connectors

## Quick Start

1. **Start the services:**
   ```bash
   docker compose up -d
   ```

2. **Wait for services to be ready (30 seconds), then submit the CDC job:**
   ```bash
   docker exec jobmanager /opt/flink/bin/sql-client.sh -f /opt/flink/job.sql
   ```

3. **Access the interfaces:**
   - Flink Web UI: http://localhost:8081
   - MinIO Console: http://localhost:9001 (admin/password123)

## Verification

### Check job status:
```bash
curl http://localhost:8081/jobs | jq .
```

### Query the Iceberg table:
```bash
docker exec jobmanager /opt/flink/bin/sql-client.sh -f /opt/flink/test_complete.sql
```

Expected output:
```
+----+-------------+--------------------------------+--------------+
| op |          id |                           name |        price |
+----+-------------+--------------------------------+--------------+
| +I |           3 |                      Product C |        39.99 |
| +I |           2 |                      Product B |        29.99 |
| +I |           1 |                      Product A |        19.99 |
+----+-------------+--------------------------------+--------------+
```

### Verify MinIO storage:
```bash
docker exec minio mc ls -r local/iceberg/warehouse/my_database/my_products/
```

## Data Flow

1. **Source**: MariaDB `products` table with sample data
2. **CDC**: MySQL CDC connector captures changes in real-time
3. **Processing**: Flink processes the change stream
4. **Sink**: Data written to Iceberg table in MinIO storage
5. **Query**: Table queryable via Flink SQL

## Configuration

The pipeline uses the following key configurations:

- **MinIO Endpoint**: `http://minio:9000`
- **Iceberg Warehouse**: `s3a://iceberg/warehouse`
- **CDC Database**: `mydatabase.products`
- **Target Table**: `minio_catalog.my_database.my_products`

## Troubleshooting

### Services not starting:
```bash
docker compose ps
docker compose logs [service-name]
```

### CDC connection issues:
```bash
# Check MariaDB
docker exec apache_flink_and_iceberg-mariadb-1 mysql -u root -prootpassword -e "SELECT * FROM mydatabase.products;"

# Check Flink logs
docker logs jobmanager
```

### MinIO access issues:
```bash
# Configure MinIO client
docker exec minio mc alias set local http://localhost:9000 admin password123
docker exec minio mc ls local/
```

## Project Structure

```
├── docker-compose.yml          # Service orchestration
├── Dockerfile                  # Custom Flink image with connectors
├── hadoop-core-site.xml        # Hadoop S3A configuration for MinIO
├── flink-config.yaml          # Flink configuration with S3 settings
├── jobs/
│   ├── job.sql                # Main CDC pipeline job
│   ├── simple_test.sql        # Simple CDC test
│   └── test_complete.sql      # End-to-end verification query
└── sql/
    ├── init.sql               # MariaDB sample data
    └── mariadb.cnf           # MariaDB CDC configuration
```

## Modernization Notes

This project has been updated from its original 2023 version with:

- ✅ Latest component versions (Flink 1.19.3, Iceberg 1.6.1)
- ✅ MinIO replaces AWS S3 for independence
- ✅ Custom Docker image approach (solves JAR classloader issues)
- ✅ Simplified credential management
- ✅ Working end-to-end data pipeline
- ✅ Comprehensive verification steps

## Development

To modify the pipeline:

1. Update SQL jobs in the `jobs/` directory
2. Rebuild and restart: `docker compose down && docker compose build --no-cache && docker compose up -d`
3. Test with verification commands above