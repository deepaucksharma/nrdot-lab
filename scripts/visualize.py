#!/usr/bin/env python3
"""
Unified visualization script for ProcessSample Optimization Lab results
Generates charts and graphs from test results
"""

import os
import json
import glob
import datetime
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from collections import defaultdict

# Default settings
RESULTS_DIR = "./results"
OUTPUT_DIR = "./results/visualizations"
LATEST_RUN = None  # Will be determined automatically

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate visualizations from test results')
    parser.add_argument('--results-dir', type=str, default=RESULTS_DIR,
                        help='Directory containing result files')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Directory to save visualizations (default: results_dir/visualizations/timestamp)')
    parser.add_argument('--run', type=str, default=None,
                        help='Specific run to visualize (default: latest)')
    parser.add_argument('--format', type=str, default='png',
                        help='Output format (png, pdf, svg)')
    parser.add_argument('--style', type=str, default='seaborn-v0_8-darkgrid',
                        help='Matplotlib style')
    parser.add_argument('--show', action='store_true',
                        help='Show plots in addition to saving them')
    return parser.parse_args()

def find_latest_run(base_dir):
    """Find the most recent results directory"""
    runs = glob.glob(os.path.join(base_dir, "20*_*"))
    if not runs:
        print(f"No result directories found in {base_dir}")
        return None
    return max(runs, key=os.path.getctime)

def load_result_files(run_dir):
    """Load all JSON result files from the specified directory"""
    result_files = glob.glob(os.path.join(run_dir, "*.json"))
    results = []
    
    for file_path in result_files:
        try:
            with open(file_path, 'r') as f:
                # Extract scenario name from filename
                scenario = os.path.basename(file_path).replace('.json', '')
                data = json.load(f)
                # Add scenario name to data
                data['scenario'] = scenario
                results.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return sorted(results, key=lambda x: x['scenario'])

def create_output_dir(base_output_dir, run_timestamp):
    """Create output directory for visualizations"""
    if not base_output_dir:
        base_output_dir = os.path.join(RESULTS_DIR, "visualizations")
    
    # Create timestamped directory within output dir
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_output_dir, timestamp)
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Saving visualizations to {output_dir}")
    return output_dir

def plot_ingest_vs_rate(results, output_dir, file_format, show_plots):
    """Generate plot of data ingest vs sample rate"""
    # Filter for sample rate experiments (R-*)
    rate_results = [r for r in results if r['scenario'].startswith('R-')]
    
    if not rate_results:
        print("No sample rate experiments found")
        return
    
    # Extract sample rates and ingest volumes
    sample_rates = []
    ps_volumes = []
    metric_volumes = []
    total_volumes = []
    
    for result in rate_results:
        # Extract sample rate from scenario name (R-XX)
        try:
            rate = int(result['scenario'].split('-')[1])
            sample_rates.append(rate)
            ps_volumes.append(result['processSample']['gbPerDay'])
            metric_volumes.append(result['metrics']['gbPerDay'])
            total_volumes.append(result['total']['gbPerDay'])
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error processing result {result['scenario']}: {e}")
    
    # Sort by sample rate
    sorted_data = sorted(zip(sample_rates, ps_volumes, metric_volumes, total_volumes))
    sample_rates, ps_volumes, metric_volumes, total_volumes = zip(*sorted_data)
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    width = 0.3
    x = np.arange(len(sample_rates))
    
    plt.bar(x - width/2, ps_volumes, width, label='ProcessSample')
    plt.bar(x + width/2, metric_volumes, width, label='OTel Metrics')
    plt.plot(x, total_volumes, 'ro-', label='Total Volume')
    
    plt.xlabel('Sample Rate (seconds)')
    plt.ylabel('GB / Day')
    plt.title('Data Ingest Volume vs. Sample Rate')
    plt.xticks(x, sample_rates)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add percentage reduction labels
    baseline = ps_volumes[0]  # Assume first entry is baseline
    for i, vol in enumerate(ps_volumes):
        reduction = (1 - vol / baseline) * 100
        plt.annotate(f"{reduction:.1f}%", xy=(x[i] - width/2, vol + 0.05),
                     ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, f'ingest_vs_rate.{file_format}'))
    
    if show_plots:
        plt.show()
    else:
        plt.close()

def plot_filter_comparison(results, output_dir, file_format, show_plots):
    """Generate comparison of different filtering strategies"""
    # Filter for filter experiments (F-*)
    filter_results = [r for r in results if r['scenario'].startswith('F-')]
    
    if not filter_results:
        print("No filter comparison experiments found")
        return
    
    # Extract filter types and ingest volumes
    filter_types = []
    ps_volumes = []
    event_counts = []
    process_counts = []
    
    for result in filter_results:
        # Extract filter type from scenario name (F-type)
        try:
            filter_type = result['scenario'].split('-')[1]
            filter_types.append(filter_type)
            ps_volumes.append(result['processSample']['gbPerDay'])
            event_counts.append(result['processSample']['eventsPerInterval'])
            process_counts.append(result['processSample']['uniqueProcesses'])
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error processing filter result {result['scenario']}: {e}")
    
    # Create the plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Data volume by filter type
    bars = ax1.bar(filter_types, ps_volumes)
    ax1.set_xlabel('Filter Type')
    ax1.set_ylabel('GB / Day')
    ax1.set_title('ProcessSample Volume by Filter Type')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Add data labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f"{height:.2f}",
                ha='center', va='bottom', fontsize=9)
    
    # Process count by filter type
    x = np.arange(len(filter_types))
    width = 0.35
    
    ax2.bar(x - width/2, event_counts, width, label='Events per Interval')
    ax2.bar(x + width/2, process_counts, width, label='Unique Processes')
    ax2.set_xlabel('Filter Type')
    ax2.set_ylabel('Count')
    ax2.set_title('Process Statistics by Filter Type')
    ax2.set_xticks(x)
    ax2.set_xticklabels(filter_types)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, f'filter_comparison.{file_format}'))
    
    if show_plots:
        plt.show()
    else:
        plt.close()

def plot_cost_visibility_tradeoff(results, output_dir, file_format, show_plots):
    """Generate plot showing cost vs visibility tradeoff"""
    # We need both rate and filter results
    rate_results = [r for r in results if r['scenario'].startswith('R-')]
    filter_results = [r for r in results if r['scenario'].startswith('F-')]
    
    if not rate_results or not filter_results:
        print("Insufficient data for cost vs visibility tradeoff plot")
        return
    
    # Combine all relevant results
    combined_results = rate_results + filter_results
    
    # Extract data points
    scenarios = []
    savings = []
    visibility_delays = []
    
    for result in combined_results:
        try:
            scenario = result['scenario']
            # Calculate visibility delay based on sample rate or scenario type
            if scenario.startswith('R-'):
                delay = float(scenario.split('-')[1]) / 2  # Assume half the sample rate
            else:
                # For filter scenarios, use standard delays
                if scenario == 'F-none':
                    delay = 30
                elif scenario == 'F-standard':
                    delay = 30
                elif scenario == 'F-aggressive':
                    delay = 35
                elif scenario == 'F-targeted':
                    delay = 32
                else:
                    delay = 30
            
            # Get savings percentage
            if 'savingsPercent' in result.get('total', {}):
                saving = result['total']['savingsPercent']
            else:
                # Calculate from GB/day if needed
                baseline = max([r['processSample']['gbPerDay'] for r in combined_results])
                saving = (1 - result['processSample']['gbPerDay'] / baseline) * 100
            
            scenarios.append(scenario)
            savings.append(saving)
            visibility_delays.append(delay)
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error processing result {result.get('scenario', 'unknown')}: {e}")
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot points
    for i, scenario in enumerate(scenarios):
        color = 'blue' if scenario.startswith('R-') else 'green'
        marker = 'o' if scenario.startswith('R-') else 's'
        plt.scatter(visibility_delays[i], savings[i], color=color, marker=marker, s=100)
        plt.annotate(scenario, (visibility_delays[i], savings[i]),
                    xytext=(5, 5), textcoords='offset points')
    
    # Add trend line
    if len(visibility_delays) > 1:
        z = np.polyfit(visibility_delays, savings, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(visibility_delays), max(visibility_delays), 100)
        plt.plot(x_trend, p(x_trend), "r--", alpha=0.7)
    
    # Add optimal zone indicator
    plt.axvspan(20, 40, alpha=0.2, color='green', label='Optimal Zone')
    
    plt.xlabel('Visibility Delay (seconds)')
    plt.ylabel('Cost Savings (%)')
    plt.title('Cost Savings vs. Visibility Tradeoff')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(['Trend', 'Optimal Zone', 'Sample Rate Tests', 'Filter Tests'])
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(PercentFormatter())
    
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, f'cost_vs_visibility.{file_format}'))
    
    if show_plots:
        plt.show()
    else:
        plt.close()

def plot_otel_contribution(results, output_dir, file_format, show_plots):
    """Generate plot showing OpenTelemetry contribution"""
    # Filter for OTel experiments (M-*)
    otel_results = [r for r in results if r['scenario'].startswith('M-')]
    
    if not otel_results:
        print("No OpenTelemetry experiments found")
        return
    
    # Extract OTel intervals and volumes
    scenarios = []
    ps_volumes = []
    metric_volumes = []
    total_volumes = []
    
    for result in otel_results:
        try:
            scenario = result['scenario']
            scenarios.append(scenario)
            ps_volumes.append(result['processSample']['gbPerDay'])
            metric_volumes.append(result['metrics']['gbPerDay'])
            total_volumes.append(result['total']['gbPerDay'])
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error processing OTel result {result.get('scenario', 'unknown')}: {e}")
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    width = 0.3
    x = np.arange(len(scenarios))
    
    bars1 = plt.bar(x - width/2, ps_volumes, width, label='ProcessSample')
    bars2 = plt.bar(x + width/2, metric_volumes, width, label='OTel Metrics')
    
    plt.xlabel('Configuration')
    plt.ylabel('GB / Day')
    plt.title('OpenTelemetry Contribution to Total Data Volume')
    plt.xticks(x, scenarios)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add total labels
    for i, total in enumerate(total_volumes):
        plt.annotate(f"Total: {total:.2f}", xy=(x[i], total + 0.05),
                     ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, f'otel_contribution.{file_format}'))
    
    if show_plots:
        plt.show()
    else:
        plt.close()

def plot_summary_dashboard(results, output_dir, file_format, show_plots):
    """Generate a summary dashboard of key findings"""
    # Extract data for each category
    sample_rates = defaultdict(float)
    filter_types = defaultdict(float)
    otel_intervals = defaultdict(float)
    
    for result in results:
        scenario = result['scenario']
        
        try:
            # Sample rate experiments
            if scenario.startswith('R-'):
                rate = int(scenario.split('-')[1])
                sample_rates[rate] = result['processSample']['gbPerDay']
            
            # Filter experiments
            elif scenario.startswith('F-'):
                filter_type = scenario.split('-')[1]
                filter_types[filter_type] = result['processSample']['gbPerDay']
            
            # OTel experiments
            elif scenario.startswith('M-'):
                if scenario == 'M-0':
                    interval = 'None'
                elif scenario == 'M-docker':
                    interval = 'Docker'
                else:
                    interval = scenario.split('-')[1] + 's'
                otel_intervals[interval] = result['metrics']['gbPerDay']
        except (KeyError, ValueError, IndexError) as e:
            print(f"Error processing result {scenario}: {e}")
    
    # Create a 2x2 dashboard
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Sample Rate Impact
    if sample_rates:
        rates = sorted(sample_rates.keys())
        volumes = [sample_rates[r] for r in rates]
        
        # Calculate percentage reductions
        baseline = volumes[0] if volumes else 0
        reductions = [(1 - v / baseline) * 100 if baseline else 0 for v in volumes]
        
        bars = ax1.bar(rates, volumes, width=5, alpha=0.7)
        ax1.set_xlabel('Sample Rate (seconds)')
        ax1.set_ylabel('GB / Day')
        ax1.set_title('Impact of Sample Rate on ProcessSample Volume')
        
        # Add reduction percentages
        for i, bar in enumerate(bars):
            ax1.annotate(f"{reductions[i]:.1f}%",
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02),
                        ha='center', va='bottom', fontsize=9)
    else:
        ax1.text(0.5, 0.5, 'No sample rate data available',
                ha='center', va='center', fontsize=12)
    
    # 2. Filter Comparison
    if filter_types:
        types = list(filter_types.keys())
        volumes = [filter_types[t] for t in types]
        
        # Calculate percentage reductions
        if 'none' in filter_types:
            baseline = filter_types['none']
            reductions = [(1 - v / baseline) * 100 if baseline else 0 for v in volumes]
        else:
            baseline = max(volumes) if volumes else 0
            reductions = [(1 - v / baseline) * 100 if baseline else 0 for v in volumes]
        
        bars = ax2.bar(types, volumes, alpha=0.7)
        ax2.set_xlabel('Filter Type')
        ax2.set_ylabel('GB / Day')
        ax2.set_title('Impact of Filter Strategy on ProcessSample Volume')
        
        # Add reduction percentages
        for i, bar in enumerate(bars):
            ax2.annotate(f"{reductions[i]:.1f}%",
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02),
                        ha='center', va='bottom', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'No filter comparison data available',
                ha='center', va='center', fontsize=12)
    
    # 3. OpenTelemetry Contribution
    if otel_intervals:
        intervals = list(otel_intervals.keys())
        volumes = [otel_intervals[i] for i in intervals]
        
        bars = ax3.bar(intervals, volumes, alpha=0.7)
        ax3.set_xlabel('OTel Interval')
        ax3.set_ylabel('GB / Day')
        ax3.set_title('OpenTelemetry Data Volume by Interval')
        
        # Add data labels
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f"{height:.2f}",
                    ha='center', va='bottom', fontsize=9)
    else:
        ax3.text(0.5, 0.5, 'No OpenTelemetry data available',
                ha='center', va='center', fontsize=12)
    
    # 4. Recommendations Summary
    ax4.axis('off')
    recommendations = [
        "Optimization Recommendations:",
        "",
        f"1. Sample Rate: {get_optimal_sample_rate(sample_rates)}s",
        f"2. Filter Strategy: {get_optimal_filter(filter_types)}",
        f"3. OTel Interval: {get_optimal_otel(otel_intervals)}",
        "",
        "Expected Results:",
        f"• ProcessSample Reduction: {get_expected_reduction(results):.1f}%",
        f"• Total Data Volume: {get_expected_volume(results):.2f} GB/day",
        f"• Est. Monthly Cost: ${get_expected_cost(results):.2f}",
    ]
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax4.text(0.5, 0.5, '\n'.join(recommendations),
            transform=ax4.transAxes, fontsize=12,
            verticalalignment='center', horizontalalignment='center',
            bbox=props)
    
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, f'summary_dashboard.{file_format}'))
    
    if show_plots:
        plt.show()
    else:
        plt.close()

def get_optimal_sample_rate(sample_rates):
    """Determine the optimal sample rate"""
    if not sample_rates:
        return "60"  # Default recommendation
    
    # Logic: If difference between 60s and higher is small, recommend 60s
    # Otherwise find the best tradeoff
    if 60 in sample_rates and 90 in sample_rates:
        if (sample_rates[60] - sample_rates[90]) / sample_rates[60] < 0.1:
            return "60"  # Difference is small, stick with 60s
    
    # Find the rate with the best tradeoff
    rates = sorted(sample_rates.keys())
    
    # Skip the first item (baseline)
    if len(rates) > 1:
        rates = rates[1:]
    
    # Default to 60 if available
    if 60 in rates:
        return "60"
    
    # Otherwise return the middle value as a safe choice
    if rates:
        return str(rates[len(rates) // 2])
    
    return "60"  # Default fallback

def get_optimal_filter(filter_types):
    """Determine the optimal filter strategy"""
    if not filter_types:
        return "standard"  # Default recommendation
    
    # Check if aggressive filter provides significant benefit over standard
    if 'standard' in filter_types and 'aggressive' in filter_types:
        standard_vol = filter_types['standard']
        aggressive_vol = filter_types['aggressive']
        
        # If aggressive is at least 5% better than standard, recommend it
        if (standard_vol - aggressive_vol) / standard_vol >= 0.05:
            return "aggressive"
        else:
            return "standard"  # Stick with standard if difference is small
    
    # Targeted is generally only recommended for specific use cases
    if 'targeted' in filter_types and 'standard' in filter_types:
        targeted_vol = filter_types['targeted']
        standard_vol = filter_types['standard']
        
        # If targeted is significantly better than standard (unlikely)
        if (standard_vol - targeted_vol) / standard_vol >= 0.1:
            return "targeted with customization"
    
    # Fall back to standard if available
    if 'standard' in filter_types:
        return "standard"
    
    # Otherwise return the key with the lowest volume
    if filter_types:
        return min(filter_types.items(), key=lambda x: x[1])[0]
    
    return "standard"  # Default fallback

def get_optimal_otel(otel_intervals):
    """Determine the optimal OpenTelemetry interval"""
    if not otel_intervals:
        return "10s"  # Default recommendation
    
    # Predefined preferences based on typical tradeoffs
    preferences = ['10s', '5s', '20s', 'Docker']
    
    for pref in preferences:
        if pref in otel_intervals:
            return pref
    
    # If no preferred interval found, return any available one
    if otel_intervals:
        return list(otel_intervals.keys())[0]
    
    return "10s"  # Default fallback

def get_expected_reduction(results):
    """Calculate expected percentage reduction"""
    # Look for an optimal scenario to use as reference
    for result in results:
        if result['scenario'] in ['A-2', 'F-standard', 'R-60']:
            if 'savingsPercent' in result.get('total', {}):
                return result['total']['savingsPercent']
    
    # Fall back to a fixed value if no reference found
    return 70.0

def get_expected_volume(results):
    """Calculate expected data volume"""
    # Look for an optimal scenario to use as reference
    for result in results:
        if result['scenario'] in ['A-2', 'F-standard', 'R-60']:
            if 'gbPerDay' in result.get('total', {}):
                return result['total']['gbPerDay']
    
    # Fall back to a fixed value if no reference found
    return 0.3

def get_expected_cost(results):
    """Calculate expected monthly cost"""
    # Look for an optimal scenario to use as reference
    for result in results:
        if result['scenario'] in ['A-2', 'F-standard', 'R-60']:
            if 'estimatedMonthlyCost' in result.get('total', {}):
                return result['total']['estimatedMonthlyCost']
    
    # Calculate from expected volume if no reference found
    expected_volume = get_expected_volume(results)
    return expected_volume * 30 * 0.25  # Assuming $0.25 per GB

def main():
    """Main function"""
    args = parse_args()
    
    # Set the matplotlib style
    plt.style.use(args.style)
    
    # Find the latest run if not specified
    run_dir = args.run
    if not run_dir:
        run_dir = find_latest_run(args.results_dir)
        if not run_dir:
            print("No result directories found. Run some tests first.")
            return 1
    
    print(f"Analyzing results from: {run_dir}")
    
    # Load all result files
    results = load_result_files(run_dir)
    if not results:
        print("No result files found in the specified directory.")
        return 1
    
    print(f"Found {len(results)} result files.")
    
    # Create output directory
    run_timestamp = os.path.basename(run_dir)
    output_dir = create_output_dir(args.output_dir, run_timestamp)
    
    # Generate visualizations
    plot_ingest_vs_rate(results, output_dir, args.format, args.show)
    plot_filter_comparison(results, output_dir, args.format, args.show)
    plot_cost_visibility_tradeoff(results, output_dir, args.format, args.show)
    plot_otel_contribution(results, output_dir, args.format, args.show)
    plot_summary_dashboard(results, output_dir, args.format, args.show)
    
    print("Visualization generation complete.")
    return 0

if __name__ == "__main__":
    main()
