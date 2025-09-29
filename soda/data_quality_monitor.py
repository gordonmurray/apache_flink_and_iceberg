#!/usr/bin/env python3

import time
import requests
import json
from datetime import datetime

# Trino connection settings
TRINO_HOST = "trino"
TRINO_PORT = 8080
CATALOG = "iceberg"
SCHEMA = "demo"

def execute_trino_query(sql):
    """Execute a query against Trino and return results"""
    headers = {
        'X-Trino-User': 'soda',
        'X-Trino-Catalog': CATALOG,
        'X-Trino-Schema': SCHEMA,
        'Content-Type': 'text/plain'
    }
    
    url = f"http://{TRINO_HOST}:{TRINO_PORT}/v1/statement"
    
    try:
        response = requests.post(url, headers=headers, data=sql)
        if response.status_code != 200:
            print(f"Error executing query: {response.status_code} - {response.text}")
            return None
            
        result = response.json()
        
        # Handle async execution with timeout
        max_polls = 50  # Maximum number of polls
        poll_count = 0
        
        while 'nextUri' in result and poll_count < max_polls:
            poll_count += 1
            time.sleep(0.2)  # Wait 200ms between polls
            response = requests.get(result['nextUri'], headers=headers)
            result = response.json()
            
            # Check if query completed
            state = result.get('stats', {}).get('state', '')
            if state in ['FINISHED', 'FAILED', 'CANCELED']:
                break
                
        if poll_count >= max_polls:
            print(f"Query timed out after {max_polls} polls")
            return None
            
        return result.get('data', [])
    except Exception as e:
        print(f"Error connecting to Trino: {e}")
        return None

def check_table_health(table_name):
    """Run basic health checks on a table"""
    print(f"\n=== {table_name.upper()} TABLE HEALTH CHECKS ===")
    
    checks = []
    
    # Row count check
    data = execute_trino_query(f"SELECT COUNT(*) as row_count FROM {table_name}")
    if data and len(data) > 0:
        row_count = data[0][0]
        checks.append(("Row count", row_count, row_count > 0, "PASS" if row_count > 0 else "FAIL"))
        print(f"✓ Row count: {row_count}")
    else:
        checks.append(("Row count", 0, False, "FAIL"))
        print(f"✗ Row count: Query failed")
    
    return checks

def check_products_quality():
    """Run specific quality checks for products table"""
    print(f"\n=== PRODUCTS DATA QUALITY CHECKS ===")
    
    checks = []
    
    # Check for null IDs
    data = execute_trino_query("SELECT COUNT(*) FROM products WHERE id IS NULL")
    if data:
        null_ids = data[0][0]
        checks.append(("Null IDs", null_ids, null_ids == 0, "PASS" if null_ids == 0 else "FAIL"))
        print(f"{'✓' if null_ids == 0 else '✗'} Null IDs: {null_ids}")
    
    # Check for null SKUs
    data = execute_trino_query("SELECT COUNT(*) FROM products WHERE sku IS NULL")
    if data:
        null_skus = data[0][0]
        checks.append(("Null SKUs", null_skus, null_skus == 0, "PASS" if null_skus == 0 else "FAIL"))
        print(f"{'✓' if null_skus == 0 else '✗'} Null SKUs: {null_skus}")
    
    # Check for duplicate SKUs
    data = execute_trino_query("SELECT COUNT(*) - COUNT(DISTINCT sku) as duplicates FROM products")
    if data:
        duplicate_skus = data[0][0]
        checks.append(("Duplicate SKUs", duplicate_skus, duplicate_skus == 0, "PASS" if duplicate_skus == 0 else "FAIL"))
        print(f"{'✓' if duplicate_skus == 0 else '✗'} Duplicate SKUs: {duplicate_skus}")
    
    # Check SKU format (should start with P-)
    data = execute_trino_query("SELECT COUNT(*) FROM products WHERE NOT regexp_like(sku, '^P-[0-9]{3}$')")
    if data:
        invalid_skus = data[0][0]
        checks.append(("Invalid SKU format", invalid_skus, invalid_skus == 0, "PASS" if invalid_skus == 0 else "FAIL"))
        print(f"{'✓' if invalid_skus == 0 else '✗'} Invalid SKU format: {invalid_skus}")
    
    return checks

def check_sales_quality():
    """Run specific quality checks for sales table"""
    print(f"\n=== SALES DATA QUALITY CHECKS ===")
    
    checks = []
    
    # Check for null quantities
    data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE qty IS NULL")
    if data:
        null_qty = data[0][0]
        checks.append(("Null quantities", null_qty, null_qty == 0, "PASS" if null_qty == 0 else "FAIL"))
        print(f"{'✓' if null_qty == 0 else '✗'} Null quantities: {null_qty}")
    
    # Check for negative quantities
    data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE qty <= 0")
    if data:
        negative_qty = data[0][0]
        checks.append(("Non-positive quantities", negative_qty, negative_qty == 0, "PASS" if negative_qty == 0 else "FAIL"))
        print(f"{'✓' if negative_qty == 0 else '✗'} Non-positive quantities: {negative_qty}")
    
    # Check for null prices
    data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE price IS NULL")
    if data:
        null_price = data[0][0]
        checks.append(("Null prices", null_price, null_price == 0, "PASS" if null_price == 0 else "FAIL"))
        print(f"{'✓' if null_price == 0 else '✗'} Null prices: {null_price}")
    
    # Check for negative prices
    data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE price <= 0")
    if data:
        negative_price = data[0][0]
        checks.append(("Non-positive prices", negative_price, negative_price == 0, "PASS" if negative_price == 0 else "FAIL"))
        print(f"{'✓' if negative_price == 0 else '✗'} Non-positive prices: {negative_price}")
    
    # Check for reasonable quantities (not too high)
    data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE qty > 100")
    if data:
        high_qty = data[0][0]
        checks.append(("Excessive quantities", high_qty, high_qty == 0, "PASS" if high_qty == 0 else "FAIL"))
        print(f"{'✓' if high_qty == 0 else '✗'} Excessive quantities (>100): {high_qty}")
    
    # Check for recent sales (within last 24 hours)
    data = execute_trino_query("SELECT COUNT(*) FROM sales WHERE sale_ts >= current_timestamp - interval '24' hour")
    if data:
        recent_sales = data[0][0]
        checks.append(("Recent sales (24h)", recent_sales, recent_sales > 0, "PASS" if recent_sales > 0 else "FAIL"))
        print(f"{'✓' if recent_sales > 0 else '✗'} Recent sales (24h): {recent_sales}")
    
    return checks

def run_data_quality_scan():
    """Run a complete data quality scan"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"DATA QUALITY SCAN - {timestamp}")
    print(f"{'='*60}")
    
    all_checks = []
    
    # Test connection
    print("\n=== CONNECTION TEST ===")
    data = execute_trino_query("SELECT 1")
    if data:
        print("✓ Successfully connected to Trino")
        all_checks.append(("Trino connection", "OK", True, "PASS"))
    else:
        print("✗ Failed to connect to Trino")
        all_checks.append(("Trino connection", "FAILED", False, "FAIL"))
        return
    
    # Run table health checks
    all_checks.extend(check_table_health("products"))
    all_checks.extend(check_table_health("sales"))
    
    # Run specific quality checks
    all_checks.extend(check_products_quality())
    all_checks.extend(check_sales_quality())
    
    # Summary
    passed = sum(1 for _, _, success, _ in all_checks if success)
    total = len(all_checks)
    
    print(f"\n{'='*60}")
    print(f"SCAN SUMMARY: {passed}/{total} checks passed")
    if passed == total:
        print("🎉 All data quality checks PASSED!")
    else:
        print(f"⚠️  {total - passed} checks FAILED - Review data quality issues")
        
        # List failed checks
        failed_checks = [name for name, _, success, _ in all_checks if not success]
        print("\nFailed checks:")
        for check in failed_checks:
            print(f"  ✗ {check}")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    print("Starting Data Quality Monitoring...")
    
    # Wait for Trino to be ready
    while True:
        try:
            response = requests.get(f"http://{TRINO_HOST}:{TRINO_PORT}/v1/info")
            if response.status_code == 200:
                print("✓ Trino is ready")
                break
        except:
            pass
        print("Waiting for Trino to be available...")
        time.sleep(10)
    
    # Run initial scan
    run_data_quality_scan()
    
    # Run periodic scans every 5 minutes
    print("\nStarting periodic monitoring (every 5 minutes)...")
    while True:
        time.sleep(300)  # 5 minutes
        run_data_quality_scan()