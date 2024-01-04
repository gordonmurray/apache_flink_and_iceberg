USE CATALOG default_catalog;

CREATE CATALOG s3_catalog WITH (
    'type' = 'iceberg',
    'catalog-type' = 'hadoop',
    'warehouse' = 's3a://my-test-bucket/iceberg',
    'property-version' = '1'
);

USE CATALOG s3_catalog;

CREATE DATABASE IF NOT EXISTS my_database;

USE my_database;

CREATE TABLE IF NOT EXISTS my_products (
    id INT PRIMARY KEY NOT ENFORCED,
    name VARCHAR,
    price DECIMAL(10, 2)
) WITH (
    'format-version'='2'
);

create temporary table products (
    id INT,
    name VARCHAR,
    price DECIMAL(10, 2),
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'connection.pool.size' = '10',
    'hostname' = 'mariadb',
    'port' = '3306',
    'username' = 'root',
    'password' = 'rootpassword',
    'database-name' = 'mydatabase',
    'table-name' = 'products'
);

SET 'execution.checkpointing.interval' = '60 s';

INSERT INTO my_products (id,name,price) SELECT id, name,price FROM products;