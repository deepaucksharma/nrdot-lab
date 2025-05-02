#!/usr/bin/env python3
"""
Visibility Latency Calculator for Windows

This script queries New Relic NerdGraph API to calculate the time delay between
when a stress-ng process starts and when it becomes visible in New Relic.
"""

import os
import json
import requests
import subprocess
from datetime import datetime, timedelta

# Environment variables
NR_API_KEY = os.environ.get('NEW_RELIC_API_KEY')
NR_ACCOUNT_ID = os.environ.get('NR_ACCOUNT_ID')

if not NR_API_KEY or not NR_ACCOUNT_ID:
    print("Error: NEW_RELIC_API_KEY or NR_ACCOUNT_ID not set")
    exit(1)

# Query to find when stress-ng process appeared in NR
query = f"""
{{
  actor {{
    account(id: {NR_ACCOUNT_ID}) {{
      nrql(query: "SELECT timestamp, cpuPercent FROM ProcessSample WHERE processDisplayName = 'stress-ng' ORDER BY timestamp ASC LIMIT 1 SINCE 1 hour ago") {{
        results
      }}
    }}
  }}
}}
"""

# Query NerdGraph API
response = requests.post(
    'https://api.newrelic.com/graphql',
    headers={
        'Content-Type': 'application/json',
        'API-Key': NR_API_KEY
    },
    json={'query': query}
)

# Parse the response
data = response.json()

try:
    # Extract the timestamp of first visible data point
    results = data['data']['actor']['account']['nrql']['results']
    if not results:
        print("0")  # No results found
        exit(0)
        
    first_visible_time = results[0]['timestamp']
    
    # Get the container start time using PowerShell
    cmd = ["powershell", "-Command", "docker inspect -f '{{.Created}}' stress-load"]
    container_start_time_str = subprocess.check_output(cmd).decode('utf-8').strip().replace("'", "")
    
    # Convert ISO strings to datetime objects
    first_visible = datetime.fromisoformat(first_visible_time.replace('Z', '+00:00'))
    container_start = datetime.fromisoformat(container_start_time_str.replace('Z', '+00:00'))
    
    # Calculate the delay in seconds
    delay_seconds = (first_visible - container_start).total_seconds()
    
    # Print just the number for capturing in scripts
    print(f"{max(0, delay_seconds):.1f}")
    
except Exception as e:
    print(f"Error calculating visibility delay: {str(e)}")
    print("0")  # Default to 0 on error
