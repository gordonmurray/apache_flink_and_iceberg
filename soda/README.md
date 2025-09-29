# Soda Core Data Quality Monitoring

This directory contains Soda Core configuration for automated data quality monitoring of your Iceberg tables.

## What's Included

### Configuration Files
- `configuration.yml`: Trino connection settings for Soda
- `checks.yml`: Data quality rules for products and sales tables
- `monitor.sh`: Monitoring script that runs checks every 5 minutes

### Data Quality Checks

**Products Table:**
- Non-empty table validation
- Null value checks (id, sku, name)
- Uniqueness validation (id, sku)
- SKU format validation (P-XXX pattern)

**Sales Table:**
- Non-empty table validation
- Null value checks (all columns)
- Business rule validation (positive quantities/prices, reasonable ranges)
- Uniqueness validation (sale id)
- Data freshness (sales within last 24 hours)
- Referential integrity (valid product_id references)

## How It Works

1. **Automatic Startup**: Soda container starts with the stack
2. **Initial Scan**: Runs data quality checks on startup
3. **Periodic Monitoring**: Checks run every 5 minutes
4. **Logging**: All results are logged to container output

## Viewing Results

Check Soda logs to see data quality results:
```bash
docker logs soda -f
```

## Customizing Checks

Edit `checks.yml` to add/modify data quality rules:
- Add new validation rules
- Modify thresholds
- Add custom SQL checks
- Configure additional tables