-- Enable streaming execution mode
SET 'execution.runtime-mode' = 'streaming';
SET 'execution.checkpointing.interval' = '60s';

-- Iceberg JDBC catalog on MySQL; data in MinIO via S3FileIO
CREATE CATALOG lake WITH (
  'type' = 'iceberg',
  'catalog-impl' = 'org.apache.iceberg.jdbc.JdbcCatalog',
  'uri' = 'jdbc:mysql://mysql:3306/iceberg_catalog',
  'jdbc.user' = 'root',
  'jdbc.password' = 'rootpw',
  'warehouse' = 's3://iceberg/warehouse',
  'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
  's3.endpoint' = 'http://minio:9000',
  's3.path-style-access' = 'true',
  's3.access-key-id' = 'minio',
  's3.secret-access-key' = 'minio123',
  'client.region' = 'us-east-1'
);

USE CATALOG lake;
USE demo;

-- CDC source for products
CREATE TEMPORARY TABLE mysql_products_stream (
  id INT,
  sku STRING,
  name STRING,
  PRIMARY KEY (id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysql',
  'port' = '3306',
  'username' = 'root',
  'password' = 'rootpw',
  'database-name' = 'appdb',
  'table-name' = 'products',
  'scan.incremental.snapshot.enabled' = 'true',
  'scan.startup.mode' = 'initial'
);

-- Stream products to Iceberg (this will run continuously)
INSERT INTO products
SELECT id, sku, name FROM mysql_products_stream;