#!/usr/bin/env python3
"""
Visualization script for ProcessSample optimization results.
Creates charts from experiment data.
"""

import os
import sys
import json
import glob
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

def find_latest_results():
    """Find the latest results directory"""
    results_dir = "./results"
    if not os.path.exists(results_dir):
        print(f"❌ Results directory not found: {results_dir}")
        sys.exit(1)
    
    # Get all timestamp directories
    timestamp_dirs = glob.glob(f"{results_dir}/*/")
    if not timestamp_dirs:
        print("❌ No result directories found")
        sys.exit(1)
    
    # Sort by directory name (timestamp)
    latest_dir = sorted(timestamp_dirs)[-1]
    return latest_dir.rstrip('/')

def extract_ingest_data(results_dir):
    """Extract ingest data from results files"""
    scenarios = {}
    
    # Look for results files
    results_files = glob.glob(f"{results_dir}/*_results.txt") + glob.glob(f"{results_dir}/*_validation.txt")
    
    for file_path in results_files:
        # Extract scenario name from filename
        scenario_name = os.path.basename(file_path).split('_')[0]
        
        # Read file and extract ingest value
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                match = re.search(r'ProcessSample ingest.*?(\d+\.\d+|\d+)', content)
                if match:
                    ingest_value = float(match.group(1))
                    scenarios[scenario_name] = ingest_value
        except Exception as e:
            print(f"Warning: Could not process {file_path}: {e}")
    
    return scenarios

def generate_bar_chart(data, output_dir):
    """Generate a bar chart comparing scenario ingest volumes"""
    if not data:
        print("❌ No data available for bar chart")
        return
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Prepare data
    scenarios = list(data.keys())
    ingest_values = list(data.values())
    
    # Color code (baseline should be red, others blue)
    colors = ['#ff6b6b' if s == 'baseline' else '#4dabf7' for s in scenarios]
    
    # Create bar chart
    plt.bar(scenarios, ingest_values, color=colors)
    
    # Add value labels on top of bars
    for i, v in enumerate(ingest_values):
        plt.text(i, v + 0.05, f"{v:.2f}", ha='center')
    
    # Calculate reduction percentages if baseline exists
    if 'baseline' in data:
        baseline_value = data['baseline']
        for i, (scenario, value) in enumerate(data.items()):
            if scenario != 'baseline':
                reduction = (1 - value / baseline_value) * 100
                plt.text(i, value / 2, f"{reduction:.1f}%\nreduction", ha='center', color='white', fontweight='bold')
    
    # Formatting
    plt.title('ProcessSample Ingest by Scenario (GB)', fontsize=14)
    plt.ylabel('Ingest Volume (GB)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save chart
    output_path = f"{output_dir}/ingest_comparison.png"
    plt.savefig(output_path)
    print(f"✅ Bar chart saved to {output_path}")
    
    return output_path

def create_markdown_report(data, chart_path, output_dir):
    """Create a Markdown report with the chart and analysis"""
    if not data:
        print("❌ No data available for report")
        return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = f"{output_dir}/visualization_report.md"
    
    with open(report_path, 'w') as f:
        f.write(f"# ProcessSample Optimization Visualization Report\n\n")
        f.write(f"Generated: {now}\n\n")
        
        f.write("## Ingest Volume Comparison\n\n")
        f.write(f"![Ingest Comparison]({os.path.basename(chart_path)})\n\n")
        
        f.write("## Data Summary\n\n")
        f.write("| Scenario | Ingest Volume (GB) | % of Baseline |\n")
        f.write("|----------|-------------------|---------------|\n")
        
        # Sort scenarios so baseline is first
        sorted_scenarios = sorted(data.keys(), key=lambda x: 0 if x == 'baseline' else 1)
        baseline_value = data.get('baseline', 1.0)
        
        for scenario in sorted_scenarios:
            value = data[scenario]
            percentage = 100 if scenario == 'baseline' else (value / baseline_value) * 100
            f.write(f"| {scenario} | {value:.3f} | {percentage:.1f}% |\n")
        
        f.write("\n## Analysis\n\n")
        
        if 'baseline' in data:
            baseline_value = data['baseline']
            reductions = []
            
            for scenario, value in data.items():
                if scenario != 'baseline':
                    reduction = (1 - value / baseline_value) * 100
                    reductions.append((scenario, reduction))
            
            if reductions:
                max_reduction = max(reductions, key=lambda x: x[1])
                f.write(f"The most effective configuration was **{max_reduction[0]}** with a **{max_reduction[1]:.1f}%** reduction in ProcessSample ingest volume compared to the baseline.\n\n")
                
                for scenario, reduction in reductions:
                    f.write(f"- **{scenario}**: {reduction:.1f}% reduction\n")
        else:
            f.write("No baseline data available for comparative analysis.\n")
    
    print(f"✅ Markdown report saved to {report_path}")
    return report_path

def main():
    """Main function"""
    print("🔍 ProcessSample Optimization Visualization Tool")
    
    # Find latest results
    results_dir = find_latest_results()
    print(f"📊 Using results from: {results_dir}")
    
    # Extract data
    data = extract_ingest_data(results_dir)
    
    if not data:
        print("❌ No ProcessSample ingest data found in result files")
        sys.exit(1)
    
    print(f"📈 Found data for {len(data)} scenarios: {', '.join(data.keys())}")
    
    # Generate visualization
    chart_path = generate_bar_chart(data, results_dir)
    
    # Create report
    if chart_path:
        report_path = create_markdown_report(data, chart_path, results_dir)
        print(f"🎉 Visualization complete! See {report_path} for the full report")

if __name__ == "__main__":
    main()
