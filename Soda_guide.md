# Soda Data Quality Monitoring Guide

This guide walks you through using the custom data quality monitoring system (Soda-equivalent) implemented in this project to verify data integrity and catch issues in your streaming data pipeline.

## Overview

Our data quality monitoring system provides:
- **Real-time monitoring** of Iceberg tables via Trino
- **Comprehensive quality checks** for business rules and data integrity
- **Automated scanning** every 5 minutes
- **Clear pass/fail reporting** with detailed diagnostics

## Quick Start

### 1. Start the Complete Stack

```bash
# Start all services including data quality monitoring
docker compose up -d

# Verify all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 2. View Data Quality Results

```bash
# Follow live data quality monitoring logs
docker logs soda -f

# View recent scan results
docker logs soda --tail 50
```

## Understanding the Output

### Successful Scan Example

```
============================================================
DATA QUALITY SCAN - 2025-09-29 11:28:23
============================================================

=== CONNECTION TEST ===
✓ Successfully connected to Trino

=== PRODUCTS TABLE HEALTH CHECKS ===
✓ Row count: 4

=== SALES TABLE HEALTH CHECKS ===
✓ Row count: 900

=== PRODUCTS DATA QUALITY CHECKS ===
✓ Null IDs: 0
✓ Null SKUs: 0
✓ Duplicate SKUs: 0
✓ Invalid SKU format: 0

=== SALES DATA QUALITY CHECKS ===
✓ Null quantities: 0
✓ Non-positive quantities: 0
✓ Null prices: 0
✓ Non-positive prices: 0
✓ Excessive quantities (>100): 0
✓ Recent sales (24h): 15

============================================================
SCAN SUMMARY: 12/12 checks passed
🎉 All data quality checks PASSED!
============================================================
```

### Failed Checks Example

```
============================================================
SCAN SUMMARY: 10/12 checks passed
⚠️  2 checks FAILED - Review data quality issues

Failed checks:
  ✗ Null prices
  ✗ Recent sales (24h)
============================================================
```

## Data Quality Checks Explained

### Products Table Checks

| Check | Purpose | What It Detects |
|-------|---------|-----------------|
| **Row count > 0** | Ensures table has data | Empty table issues |
| **Null IDs: 0** | Primary key integrity | Missing primary keys |
| **Null SKUs: 0** | Business key integrity | Missing business identifiers |
| **Duplicate SKUs: 0** | Uniqueness validation | Data duplication issues |
| **Invalid SKU format: 0** | Format validation | SKUs not matching P-XXX pattern |

### Sales Table Checks

| Check | Purpose | What It Detects |
|-------|---------|-----------------|
| **Row count > 0** | Ensures table has data | Empty table issues |
| **Null quantities: 0** | Required field validation | Missing transaction data |
| **Non-positive quantities: 0** | Business rule validation | Invalid quantities (≤ 0) |
| **Null prices: 0** | Required field validation | Missing price data |
| **Non-positive prices: 0** | Business rule validation | Invalid prices (≤ 0) |
| **Excessive quantities: 0** | Outlier detection | Unrealistic quantities (> 100) |
| **Recent sales (24h) > 0** | Data freshness validation | Stale data detection |

## Testing Data Quality Monitoring

### Test 1: Insert Valid Data

```bash
# Insert a valid new sale
docker exec mysql mysql -u root -prootpw -e "
  INSERT INTO appdb.sales (product_id, qty, price, sale_ts) 
  VALUES (1, 5, 19.99, NOW());
"

# Wait for CDC to process (30-60 seconds)
sleep 60

# Check if monitoring detects the new data
docker logs soda --tail 20
```

**Expected Result:** Recent sales check should now pass.

### Test 2: Insert Invalid Data (Negative Price)

```bash
# Insert invalid data to trigger quality alerts
docker exec mysql mysql -u root -prootpw -e "
  INSERT INTO appdb.sales (product_id, qty, price, sale_ts) 
  VALUES (2, 3, -10.50, NOW());
"

# Wait for CDC to process
sleep 60

# Check monitoring results
docker logs soda --tail 30
```

**Expected Result:** "Non-positive prices" check should fail.

### Test 3: Insert Invalid Product

```bash
# Insert product with invalid SKU format
docker exec mysql mysql -u root -prootpw -e "
  INSERT INTO appdb.products (sku, name) 
  VALUES ('INVALID-SKU', 'Test Product');
"

# Wait for CDC to process
sleep 60

# Check monitoring results
docker logs soda --tail 30
```

**Expected Result:** "Invalid SKU format" check should fail.

## Advanced Usage

### Manual Data Quality Scan

Run an immediate scan without waiting for the scheduled interval:

```bash
# Execute a manual scan
docker exec soda python data_quality_monitor.py
```

### Check Specific Data Issues

```bash
# Query Trino directly to investigate issues
docker exec trino trino --execute "
  SELECT COUNT(*) as negative_prices 
  FROM iceberg.demo.sales 
  WHERE price <= 0;
"

# Check for recent data
docker exec trino trino --execute "
  SELECT COUNT(*) as recent_sales
  FROM iceberg.demo.sales 
  WHERE sale_ts >= current_timestamp - interval '24' hour;
"

# Check product SKU formats
docker exec trino trino --execute "
  SELECT sku, name 
  FROM iceberg.demo.products 
  WHERE NOT regexp_like(sku, '^P-[0-9]{3}$');
"
```

### View Raw Data

```bash
# Check products
docker exec trino trino --execute "SELECT * FROM iceberg.demo.products LIMIT 10;"

# Check recent sales
docker exec trino trino --execute "
  SELECT product_id, qty, price, sale_ts 
  FROM iceberg.demo.sales 
  ORDER BY sale_ts DESC 
  LIMIT 10;
"
```

## Monitoring Schedule

The data quality monitoring runs:
- **Initial scan** on startup
- **Periodic scans** every 5 minutes
- **Continuous monitoring** until stopped

## Customizing Quality Checks

### Adding New Checks

Edit `/soda/data_quality_monitor.py` to add custom checks:

```python
# Add to check_sales_quality() function
def check_sales_quality():
    # ... existing checks ...
    
    # Custom check: Average order value
    data = execute_trino_query("SELECT AVG(price * qty) FROM sales")
    if data:
        avg_order_value = data[0][0]
        is_valid = avg_order_value > 10.0  # Minimum $10 AOV
        status = "PASS" if is_valid else "FAIL"
        print(f"{'✓' if is_valid else '✗'} Average order value: ${avg_order_value:.2f}")
        checks.append(("Average order value", avg_order_value, is_valid, status))
```

### Modifying Check Thresholds

```python
# Change quantity threshold from 100 to 50
data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE qty > 50")

# Change freshness window from 24 hours to 1 hour
data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE sale_ts >= current_timestamp - interval '1' hour")
```

## Troubleshooting

### No Recent Data Detection

If the "Recent sales" check fails:

1. **Check if new data was inserted:**
   ```bash
   docker exec mysql mysql -u root -prootpw -e "SELECT MAX(sale_ts) FROM appdb.sales;"
   ```

2. **Verify CDC is running:**
   ```bash
   curl -s http://localhost:8081/jobs | python3 -m json.tool
   ```

3. **Check Flink job logs:**
   ```bash
   docker logs jobmanager --tail 50
   ```

### Connection Issues

If monitoring can't connect to Trino:

1. **Check Trino status:**
   ```bash
   curl -s http://localhost:8080/v1/info | python3 -m json.tool
   ```

2. **Verify network connectivity:**
   ```bash
   docker exec soda python -c "import requests; print(requests.get('http://trino:8080/v1/info').status_code)"
   ```

### Missing Tables

If tables don't exist:

1. **Submit Flink jobs:**
   ```bash
   docker exec jobmanager /opt/flink/bin/sql-client.sh -f /opt/flink/job.sql
   ```

2. **Check table creation:**
   ```bash
   docker exec trino trino --execute "SHOW TABLES IN iceberg.demo;"
   ```

## Integration with CI/CD

### Pre-deployment Validation

```bash
#!/bin/bash
# Run data quality scan and exit with error if checks fail

# Start monitoring scan
SCAN_OUTPUT=$(docker exec soda python data_quality_monitor.py)

# Check if all tests passed
if echo "$SCAN_OUTPUT" | grep -q "All data quality checks PASSED"; then
    echo "✅ Data quality validation passed"
    exit 0
else
    echo "❌ Data quality validation failed"
    echo "$SCAN_OUTPUT"
    exit 1
fi
```

### Alerting Integration

Add webhook notifications for failed checks:

```python
import requests

def send_alert(failed_checks):
    webhook_url = "https://your-webhook-url"
    message = f"Data Quality Alert: {len(failed_checks)} checks failed"
    
    payload = {
        "text": message,
        "checks": failed_checks
    }
    
    requests.post(webhook_url, json=payload)
```

## Best Practices

1. **Monitor Regularly:** Check logs daily for any quality issues
2. **Set Thresholds:** Adjust check thresholds based on your business rules
3. **Test Changes:** Always test data quality after schema or pipeline changes
4. **Document Issues:** Keep track of recurring quality issues and their resolutions
5. **Automate Responses:** Consider automated responses for critical failures

## Configuration Files

The monitoring system uses these key files:
- `/soda/data_quality_monitor.py` - Main monitoring script
- `/soda/configuration.yml` - Trino connection settings (legacy Soda format)
- `/soda/checks.yml` - Quality check definitions (legacy Soda format)

## Performance Considerations

- **Scan Frequency:** Default 5-minute intervals balance freshness vs. resource usage
- **Query Optimization:** Complex checks may need optimization for large datasets
- **Resource Limits:** Monitor container resource usage during scans

---

## Quick Reference Commands

```bash
# View live monitoring
docker logs soda -f

# Manual scan
docker exec soda python data_quality_monitor.py

# Check data freshness
docker exec trino trino --execute "SELECT MAX(sale_ts) FROM iceberg.demo.sales;"

# View failed data
docker exec trino trino --execute "SELECT * FROM iceberg.demo.sales WHERE price <= 0;"

# Restart monitoring
docker compose restart soda
```

This monitoring system provides production-ready data quality validation equivalent to Soda Core, ensuring your streaming data pipeline maintains high data integrity standards!