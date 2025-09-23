SET sql-client.execution.result-mode=TABLEAU;

USE CATALOG default_catalog;

CREATE CATALOG minio_catalog WITH (
    'type' = 'iceberg',
    'catalog-type' = 'hadoop',
    'warehouse' = 's3a://iceberg/warehouse',
    'property-version' = '1'
);

USE CATALOG minio_catalog;
USE my_database;
SELECT * FROM my_products;