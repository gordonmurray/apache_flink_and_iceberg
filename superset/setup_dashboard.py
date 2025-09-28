#!/usr/bin/env python3

import requests
import json
import time
import sys

# Superset configuration
SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"

def login():
    """Login to Superset and get access token"""
    session = requests.Session()
    
    # Get CSRF token
    resp = session.get(f"{SUPERSET_URL}/login/")
    if resp.status_code != 200:
        print(f"Failed to get login page: {resp.status_code}")
        return None
        
    # Login
    login_data = {
        "username": USERNAME,
        "password": PASSWORD,
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/security/login", json=login_data)
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return None
        
    access_token = resp.json().get("access_token")
    if not access_token:
        print("No access token received")
        return None
        
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    return session

def create_database_connection(session):
    """Create Trino database connection"""
    print("Creating Trino database connection...")
    
    database_data = {
        "database_name": "Trino Iceberg",
        "sqlalchemy_uri": "trino://trino:8080/iceberg",
        "expose_in_sqllab": True,
        "allow_ctas": True,
        "allow_cvas": True,
        "allow_dml": True,
        "allow_run_async": True
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/database/", json=database_data)
    if resp.status_code == 201:
        db_id = resp.json()["id"]
        print(f"Database connection created successfully with ID: {db_id}")
        return db_id
    elif resp.status_code == 422:
        # Database might already exist, try to find it
        resp = session.get(f"{SUPERSET_URL}/api/v1/database/")
        if resp.status_code == 200:
            databases = resp.json()["result"]
            for db in databases:
                if "trino" in db["database_name"].lower():
                    print(f"Found existing Trino database with ID: {db['id']}")
                    return db["id"]
    
    print(f"Failed to create database connection: {resp.status_code} - {resp.text}")
    return None

def create_dataset(session, database_id):
    """Create dataset for sales table"""
    print("Creating sales dataset...")
    
    dataset_data = {
        "database": database_id,
        "schema": "demo",
        "table_name": "sales"
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/dataset/", json=dataset_data)
    if resp.status_code == 201:
        dataset_id = resp.json()["id"]
        print(f"Sales dataset created successfully with ID: {dataset_id}")
        return dataset_id
    elif resp.status_code == 422:
        # Dataset might already exist, try to find it
        resp = session.get(f"{SUPERSET_URL}/api/v1/dataset/")
        if resp.status_code == 200:
            datasets = resp.json()["result"]
            for ds in datasets:
                if ds["table_name"] == "sales":
                    print(f"Found existing sales dataset with ID: {ds['id']}")
                    return ds["id"]
    
    print(f"Failed to create dataset: {resp.status_code} - {resp.text}")
    return None

def create_chart(session, dataset_id):
    """Create sales count chart"""
    print("Creating sales count chart...")
    
    chart_data = {
        "slice_name": "Sales Count by Product",
        "viz_type": "pie",
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps({
            "groupby": ["product_id"],
            "metric": "count",
            "viz_type": "pie",
            "row_limit": 10000
        })
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/chart/", json=chart_data)
    if resp.status_code == 201:
        chart_id = resp.json()["id"]
        print(f"Chart created successfully with ID: {chart_id}")
        return chart_id
    
    print(f"Failed to create chart: {resp.status_code} - {resp.text}")
    return None

def create_sales_volume_chart(session, dataset_id):
    """Create sales volume chart"""
    print("Creating sales volume chart...")
    
    chart_data = {
        "slice_name": "Total Sales Volume",
        "viz_type": "big_number_total",
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metric": "sum__qty",
            "viz_type": "big_number_total"
        })
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/chart/", json=chart_data)
    if resp.status_code == 201:
        chart_id = resp.json()["id"]
        print(f"Sales volume chart created successfully with ID: {chart_id}")
        return chart_id
    
    print(f"Failed to create sales volume chart: {resp.status_code} - {resp.text}")
    return None

def create_revenue_chart(session, dataset_id):
    """Create total revenue chart"""
    print("Creating total revenue chart...")
    
    chart_data = {
        "slice_name": "Total Revenue",
        "viz_type": "big_number_total",
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps({
            "metric": "sum__price",
            "viz_type": "big_number_total"
        })
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/chart/", json=chart_data)
    if resp.status_code == 201:
        chart_id = resp.json()["id"]
        print(f"Revenue chart created successfully with ID: {chart_id}")
        return chart_id
    
    print(f"Failed to create revenue chart: {resp.status_code} - {resp.text}")
    return None

def create_dashboard(session, chart_ids):
    """Create dashboard with charts"""
    print("Creating sales dashboard...")
    
    # Create position json for dashboard layout
    position_json = {
        "CHART-1": {
            "children": [],
            "id": "CHART-1",
            "meta": {"chartId": chart_ids[0], "width": 6, "height": 50},
            "type": "CHART"
        },
        "CHART-2": {
            "children": [],
            "id": "CHART-2", 
            "meta": {"chartId": chart_ids[1], "width": 3, "height": 50},
            "type": "CHART"
        },
        "CHART-3": {
            "children": [],
            "id": "CHART-3",
            "meta": {"chartId": chart_ids[2], "width": 3, "height": 50},
            "type": "CHART"
        },
        "GRID_ID": {
            "children": ["ROW-1"],
            "id": "GRID_ID",
            "type": "GRID"
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "meta": {"text": "Sales Analytics Dashboard"},
            "type": "HEADER"
        },
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "type": "ROOT"
        },
        "ROW-1": {
            "children": ["CHART-2", "CHART-3", "CHART-1"],
            "id": "ROW-1",
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "type": "ROW"
        }
    }
    
    dashboard_data = {
        "dashboard_title": "Sales Analytics Dashboard",
        "slug": "sales-analytics",
        "owners": [1],
        "position_json": json.dumps(position_json),
        "slices": chart_ids
    }
    
    resp = session.post(f"{SUPERSET_URL}/api/v1/dashboard/", json=dashboard_data)
    if resp.status_code == 201:
        dashboard_id = resp.json()["id"]
        print(f"Dashboard created successfully with ID: {dashboard_id}")
        print(f"Access the dashboard at: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")
        return dashboard_id
    
    print(f"Failed to create dashboard: {resp.status_code} - {resp.text}")
    return None

def main():
    print("Configuring Superset for Trino/Iceberg integration...")
    
    # Wait for Superset to be ready
    print("Waiting for Superset to be ready...")
    for i in range(30):
        try:
            resp = requests.get(f"{SUPERSET_URL}/health")
            if resp.status_code == 200:
                break
        except:
            pass
        time.sleep(2)
    else:
        print("Superset is not ready after 60 seconds")
        sys.exit(1)
    
    # Login
    session = login()
    if not session:
        print("Failed to login to Superset")
        sys.exit(1)
    
    # Create database connection
    database_id = create_database_connection(session)
    if not database_id:
        print("Failed to create database connection")
        sys.exit(1)
    
    # Create dataset
    dataset_id = create_dataset(session, database_id)
    if not dataset_id:
        print("Failed to create dataset")
        sys.exit(1)
    
    # Create charts
    chart_ids = []
    
    chart_id = create_chart(session, dataset_id)
    if chart_id:
        chart_ids.append(chart_id)
    
    volume_chart_id = create_sales_volume_chart(session, dataset_id)
    if volume_chart_id:
        chart_ids.append(volume_chart_id)
        
    revenue_chart_id = create_revenue_chart(session, dataset_id)
    if revenue_chart_id:
        chart_ids.append(revenue_chart_id)
    
    if not chart_ids:
        print("Failed to create any charts")
        sys.exit(1)
    
    # Create dashboard
    dashboard_id = create_dashboard(session, chart_ids)
    if not dashboard_id:
        print("Failed to create dashboard")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")
    print(f"🌐 Superset: {SUPERSET_URL}")
    print(f"👤 Login: {USERNAME}/{PASSWORD}")
    print(f"📊 Dashboard: {SUPERSET_URL}/superset/dashboard/{dashboard_id}/")

if __name__ == "__main__":
    main()