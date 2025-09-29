# Superset + Trino + Iceberg Integration

## Configuration Details

### Database Connection
- **Database Name**: "Trino Iceberg"
- **Connection URI**: `trino://admin@trino:8080/iceberg`
- **Configured via**: Superset CLI (`superset set-database-uri`)
- **Note**: Username 'admin' required for Trino authentication

### Data Available
- **Sales Table**: `iceberg.demo.sales` (903+ records)
- **Products Table**: `iceberg.demo.products` (5 records)

### Access Information
- **Superset UI**: http://localhost:8088
- **Credentials**: admin / admin
- **Trino Coordinator**: http://localhost:8080

## Sample Dashboard Queries

The following queries work in Superset SQL Lab:

```sql
-- Sales count by product
SELECT p.name, COUNT(s.id) as sales_count
FROM demo.sales s
JOIN demo.products p ON s.product_id = p.id
GROUP BY p.name
ORDER BY sales_count DESC;

-- Revenue by product
SELECT p.name, SUM(s.price * s.qty) as total_revenue
FROM demo.sales s
JOIN demo.products p ON s.product_id = p.id
GROUP BY p.name
ORDER BY total_revenue DESC;

-- Daily sales trends
SELECT DATE(sale_ts) as sale_date, COUNT(*) as daily_sales
FROM demo.sales
GROUP BY DATE(sale_ts)
ORDER BY sale_date;
```

## Dashboard Creation Steps

1. **Access Superset**: http://localhost:8088 (admin/admin)
2. **SQL Lab**: Test queries with "Trino Iceberg" database
3. **Create Charts**: Charts → + → Select "Trino Iceberg" → demo.sales table
4. **Build Dashboard**: Dashboards → + → Add created charts
