#!/usr/bin/env python3
"""
Results Visualization Generator

This script processes all result JSON files and generates visualizations:
1. Ingest vs. Sample Rate plot
2. Cost vs. Visibility Latency scatter plot
"""

import os
import json
import glob
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def load_all_results():
    """Load all results JSON files from the results directory."""
    results = []
    for result_file in glob.glob('results/*/*.json'):
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                # Extract run date from directory path
                run_date = os.path.basename(os.path.dirname(result_file))
                data['run_date'] = run_date
                results.append(data)
        except Exception as e:
            print(f"Error loading {result_file}: {str(e)}")
    return results

def group_by_run_date(results):
    """Group results by run date."""
    grouped = {}
    for result in results:
        run_date = result.get('run_date')
        if run_date not in grouped:
            grouped[run_date] = []
        grouped[run_date].append(result)
    return grouped

def plot_ingest_vs_sample_rate(results, run_date, output_dir):
    """Generate plot showing ingest vs sample rate."""
    # Filter for rate-sweep scenarios (R-* pattern)
    rate_sweep = [r for r in results if r.get('scenario_id', '').startswith('R-')]
    
    if not rate_sweep:
        print(f"No rate sweep data for {run_date}")
        return
    
    # Sort by sample rate
    rate_sweep.sort(key=lambda x: int(x.get('current_rate', 0)))
    
    rates = [int(r.get('current_rate', 0)) for r in rate_sweep]
    daily_gb = [float(r.get('daily_gb', 0)) for r in rate_sweep]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(rates, daily_gb, 'o-', linewidth=2, markersize=8)
    plt.xlabel('Sample Rate (seconds)', fontsize=12)
    plt.ylabel('Daily Ingest (GB)', fontsize=12)
    plt.title(f'ProcessSample Ingest vs Sample Rate - {run_date}', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add value annotations
    for i, (rate, gb) in enumerate(zip(rates, daily_gb)):
        plt.annotate(f"{gb:.2f} GB", 
                    xy=(rate, gb),
                    xytext=(5, 5),
                    textcoords='offset points')
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/ingest_vs_rate_{run_date}.png", dpi=300, bbox_inches='tight')
    plt.close()

def plot_cost_vs_visibility(results, run_date, output_dir):
    """Generate scatter plot of cost vs visibility delay."""
    # Filter for scenarios that have visibility delay measurements
    valid_results = [r for r in results if 'visibility_delay_s' in r and 'daily_gb' in r]
    
    if not valid_results:
        print(f"No visibility delay data for {run_date}")
        return
    
    # Extract data
    daily_gb = [float(r.get('daily_gb', 0)) for r in valid_results]
    delay_s = [float(r.get('visibility_delay_s', 0)) for r in valid_results]
    labels = [r.get('scenario_id', 'unknown') for r in valid_results]
    
    # Create the scatter plot
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(daily_gb, delay_s, s=100, alpha=0.7)
    
    plt.xlabel('Daily Ingest (GB)', fontsize=12)
    plt.ylabel('Visibility Delay (seconds)', fontsize=12)
    plt.title(f'Cost vs Visibility Trade-off - {run_date}', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add labels for each point
    for i, label in enumerate(labels):
        plt.annotate(label, 
                    xy=(daily_gb[i], delay_s[i]),
                    xytext=(5, 5),
                    textcoords='offset points')
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(f"{output_dir}/cost_vs_visibility_{run_date}.png", dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Load all results
    results = load_all_results()
    if not results:
        print("No results found")
        return
    
    # Group by run date
    grouped_results = group_by_run_date(results)
    
    # Generate plots for each run date
    for run_date, run_results in grouped_results.items():
        output_dir = f"results/visualizations/{run_date}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Generating plots for {run_date}...")
        plot_ingest_vs_sample_rate(run_results, run_date, output_dir)
        plot_cost_vs_visibility(run_results, run_date, output_dir)
        
    print("Visualization generation complete")

if __name__ == "__main__":
    main()
