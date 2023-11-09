# Trying out Apache Iceberg with Apache Flink using Docker Compose

Created the following docker-compose.yml file to create a mariadb database and a flink job/task manager to work with.

You'll need to include JAR files for s3 storage as well as ICeberg. All the JARs needed are in the jars folder and included in the docker compose file.
```
version: '3.7'

services:
  mariadb:
    image: mariadb:10.6.14
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
    volumes:
      - ./sql/mariadb.cnf:/etc/mysql/mariadb.conf.d/mariadb.cnf
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"

  jobmanager:
    image: flink:1.17.1
    container_name: jobmanager
    environment:
      - JOB_MANAGER_RPC_ADDRESS=jobmanager
      - AWS_ACCESS_KEY_ID=xxxxx
      - AWS_SECRET_ACCESS_KEY=xxxxx
    ports:
      - "8081:8081"
    command: jobmanager
    volumes:
      - ./jars/flink-sql-connector-mysql-cdc-2.4.1.jar:/opt/flink/lib/flink-sql-connector-mysql-cdc-2.4.1.jar
      - ./jars/flink-connector-jdbc-3.1.0-1.17.jar:/opt/flink/lib/flink-connector-jdbc-3.1.0-1.17.jar
      - ./jars/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar:/opt/flink/lib/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar
      - ./jars/flink-s3-fs-hadoop-1.17.1.jar:/opt/flink/lib/flink-s3-fs-hadoop-1.17.1.jar
      - ./jars/iceberg-flink-runtime-1.17-1.4.2.jar:/opt/flink/lib/iceberg-flink-runtime-1.17-1.4.2.jar
      - ./jars/hadoop-mapreduce-client-core-3.3.4.jar:/opt/flink/lib/hadoop-mapreduce-client-core-3-3.4.jar
      - ./jars/hadoop-hdfs-client-3.2.1.jar:/opt/flink/lib/hadoop-hdfs-client-3.2.1.jar
      - ./jars/hadoop-aws-3.3.4.jar:/opt/flink/lib/hadoop-aws-3.3.4.jar
      - ./jobs/job.sql:/opt/flink/job.sql
    deploy:
          replicas: 1
  taskmanager:
    image: flink:1.17.1
    environment:
      - JOB_MANAGER_RPC_ADDRESS=jobmanager
      - AWS_ACCESS_KEY_ID=xxxxx
      - AWS_SECRET_ACCESS_KEY=xxxxx
    depends_on:
      - jobmanager
    command: taskmanager
    volumes:
      - ./jars/flink-sql-connector-mysql-cdc-2.4.1.jar:/opt/flink/lib/flink-sql-connector-mysql-cdc-2.4.1.jar
      - ./jars/flink-connector-jdbc-3.1.0-1.17.jar:/opt/flink/lib/flink-connector-jdbc-3.1.0-1.17.jar
      - ./jars/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar:/opt/flink/lib/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar
      - ./jars/flink-s3-fs-hadoop-1.17.1.jar:/opt/flink/lib/flink-s3-fs-hadoop-1.17.1.jar
      - ./jars/iceberg-flink-runtime-1.17-1.4.2.jar:/opt/flink/lib/iceberg-flink-runtime-1.17-1.4.2.jar
      - ./jars/hadoop-mapreduce-client-core-3.3.4.jar:/opt/flink/lib/hadoop-mapreduce-client-core-3-3.4.jar
      - ./jars/hadoop-hdfs-client-3.2.1.jar:/opt/flink/lib/hadoop-hdfs-client-3.2.1.jar
      - ./jars/hadoop-aws-3.3.4.jar:/opt/flink/lib/hadoop-aws-3.3.4.jar
    deploy:
          replicas: 2

```

To create a little Flink cluster along with a Mariadb database to read from first update the docker compose file to include your AWS credentials to write to s3 then run docker compose using:

```
docker compose up -d
```

Once running, submit the job to Flink using:image

```
docker exec -it jobmanager /opt/flink/bin/sql-client.sh embedded -f job.sql
```

If you open your browser to `http://localhost:8081` you'll see the Flink UI ith your job running, saving the data from the database to s3 using the Iceberg format

![Flink UI](flink.png)

The data in s3 will be in a folder named after the database.

![s3 folder structure](s3.png)