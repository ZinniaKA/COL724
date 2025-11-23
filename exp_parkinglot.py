#!/usr/bin/env python3
"""
Batch Experiment Runner for QUIC Parking Lot Topology
Runs experiments with varying bandwidth, delay, and loss parameters
"""

import os
import sys
import subprocess
import csv
from datetime import datetime

# Experiment parameters
BANDWIDTHS = [10, 15, 20, 35]  # Mbps
DELAYS = ["1ms", "2ms", "5ms", "10ms"]
LOSSES = [0, 2, 5, 10]  # Percentage
DURATION = 60  # seconds
TOPOLOGY = "parkinglot"

# Fixed parameters for control experiments
FIXED_BW = 15
FIXED_DELAY = "2ms"
FIXED_LOSS = 2

# Base results directory
RESULTS_DIR = "parkinglot_results"
EXPERIMENT_RUNNER = "experiment_runner_quic.py"


def run_experiment(bw, delay, loss, duration, output_dir):
    
    cmd = [
        "sudo", "python3", EXPERIMENT_RUNNER,
        "--topo", TOPOLOGY,
        "--bw", str(bw),
        "--delay", delay,
        "--loss", str(loss),
        "--duration", str(duration),
        "--output-dir", output_dir
    ]
    
    # print(f"\n{'='*70}")
    print(f"Running: bw={bw}Mbps, delay={delay}, loss={loss}%")
    # print(f"Output: {output_dir}")
    # print(f"{'='*70}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"Experiment completed successfully")
        print(f"{'='*70}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Experiment failed with return code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\nExperiment interrupted by user")
        return False


def extract_results(output_dir):
    """Extract throughput and average RTT from experiment results"""
    
    switches_file = os.path.join(output_dir, "switches.csv")
    rtt_file = os.path.join(output_dir, "rtt.csv")
    
    try:
        if not os.path.exists(switches_file) or not os.path.exists(rtt_file):
            print(f"  ⚠ Warning: Could not find result files in {output_dir}")
            return None
        
        throughputs = {}
        total_throughput = 0
        
        with open(switches_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                interface = row['interface']
                throughput = float(row['throughput_mbps'])
                throughputs[interface] = throughput
                total_throughput += throughput
        
        # Get individual bottleneck throughputs
        bottleneck1_throughput = throughputs.get('s1-eth21', 0)  # First bottleneck (s1 -> s2)
        bottleneck2_throughput = throughputs.get('s2-eth12', 0)  # Second bottleneck (s2 -> s3)
        
        # Extract average RTT from rtt file
        rtts = []
        with open(rtt_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rtts.append(float(row['avg_rtt_ms']))
        
        avg_rtt = sum(rtts) / len(rtts) if rtts else 0
        
        return {
            'bottleneck1_throughput_mbps': round(bottleneck1_throughput, 2),
            'bottleneck2_throughput_mbps': round(bottleneck2_throughput, 2),
            # 'total_throughput_mbps': round(total_throughput, 2),
            'avg_rtt_ms': round(avg_rtt, 2)
        }
        
    except Exception as e:
        print(f"Error extracting results: {e}")
        return None


def run_varying_bandwidth():
    """Run experiments with varying bandwidth (fixed delay and loss)"""
    
    print(f"\n{'#'*70}")
    print(f"# Experiment Set 1: Varying Bandwidth")
    print(f"# Fixed: delay={FIXED_DELAY}, loss={FIXED_LOSS}%")
    print(f"{'#'*70}")
    
    results = []
    
    for bw in BANDWIDTHS:
        output_dir = os.path.join(RESULTS_DIR, f"bw_vary/bw{bw}_delay{FIXED_DELAY}_loss{FIXED_LOSS}")
        
        if run_experiment(bw, FIXED_DELAY, FIXED_LOSS, DURATION, output_dir):
            metrics = extract_results(output_dir)
            if metrics:
                results.append({
                    'bandwidth_mbps': bw,
                    'delay': FIXED_DELAY,
                    'loss_pct': FIXED_LOSS,
                    **metrics
                })
    
    # Save summary
    summary_file = os.path.join(RESULTS_DIR, "bw_vary/summary.csv")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    
    with open(summary_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            print(f"\n✓Summary saved")


def run_varying_delay():
    """Run experiments with varying delay (fixed bandwidth and loss)"""
    
    print(f"\n{'#'*70}")
    print(f"# Experiment Set 2: Varying Delay")
    print(f"# Fixed: bandwidth={FIXED_BW}Mbps, loss={FIXED_LOSS}%")
    print(f"{'#'*70}")
    
    results = []
    
    for delay in DELAYS:
        output_dir = os.path.join(RESULTS_DIR, f"delay_vary/bw{FIXED_BW}_delay{delay}_loss{FIXED_LOSS}")
        
        if run_experiment(FIXED_BW, delay, FIXED_LOSS, DURATION, output_dir):
            metrics = extract_results(output_dir)
            if metrics:
                results.append({
                    'bandwidth_mbps': FIXED_BW,
                    'delay': delay,
                    'loss_pct': FIXED_LOSS,
                    **metrics
                })
    
    # Save summary
    summary_file = os.path.join(RESULTS_DIR, "delay_vary/summary.csv")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    
    with open(summary_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            print(f"\nSummary saved")


def run_varying_loss():
    """Run experiments with varying loss (fixed bandwidth and delay)"""
    
    print(f"\n{'#'*70}")
    print(f"# Experiment Set 3: Varying Loss")
    print(f"# Fixed: bandwidth={FIXED_BW}Mbps, delay={FIXED_DELAY}")
    print(f"{'#'*70}")
    
    results = []
    
    for loss in LOSSES:
        output_dir = os.path.join(RESULTS_DIR, f"loss_vary/bw{FIXED_BW}_delay{FIXED_DELAY}_loss{loss}")
        
        if run_experiment(FIXED_BW, FIXED_DELAY, loss, DURATION, output_dir):
            metrics = extract_results(output_dir)
            if metrics:
                results.append({
                    'bandwidth_mbps': FIXED_BW,
                    'delay': FIXED_DELAY,
                    'loss_pct': loss,
                    **metrics
                })
    
    # Save summary
    summary_file = os.path.join(RESULTS_DIR, "loss_vary/summary.csv")
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    
    with open(summary_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
            print(f"\nSummary saved")


def print_summary_statistics():
    """Print overall summary of all experiments"""
    
    print(f"\n{'='*70}")
    print(f"EXPERIMENT SUMMARY")
    print(f"{'='*70}")
    
    # Load all summary files
    summaries = {
        'Varying Bandwidth': os.path.join(RESULTS_DIR, "bw_vary/summary.csv"),
        'Varying Delay': os.path.join(RESULTS_DIR, "delay_vary/summary.csv"),
        'Varying Loss': os.path.join(RESULTS_DIR, "loss_vary/summary.csv")
    }
    
    for name, summary_file in summaries.items():
        if os.path.exists(summary_file):
            print(f"\n{name}:")
            print(f"-" * 70)
            with open(summary_file, 'r') as f:
                reader = csv.DictReader(f)
                print(f"{'BW':<6} {'Delay':<8} {'Loss':<6} {'B1 Tput':<10} {'B2 Tput':<10} {'Total':<10} {'Avg RTT':<10}")
                print(f"{'(Mbps)':<6} {'':<8} {'(%)':<6} {'(Mbps)':<10} {'(Mbps)':<10} {'(Mbps)':<10} {'(ms)':<10}")
                print(f"-" * 70)
                for row in reader:
                    print(f"{row['bandwidth_mbps']:<6} {row['delay']:<8} {row['loss_pct']:<6} "
                          f"{row['bottleneck1_throughput_mbps']:<10} "
                          f"{row['bottleneck2_throughput_mbps']:<10} "
                          f"{row['total_throughput_mbps']:<10} "
                          f"{row['avg_rtt_ms']:<10}")


def main():
    """Main experiment orchestrator"""
    
    # Check if experiment runner exists
    if not os.path.exists(EXPERIMENT_RUNNER):
        print(f"Error: Experiment runner '{EXPERIMENT_RUNNER}' not found!")
        print(f"Please ensure the file is in the current directory.")
        sys.exit(1)
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Record start time
    start_time = datetime.now()
    print(f"\n{'='*70}")
    print(f"QUIC PARKING LOT TOPOLOGY - BATCH EXPERIMENTS")
    print(f"{'='*70}")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration per experiment: {DURATION} seconds")
    print(f"Total experiments: {len(BANDWIDTHS) + len(DELAYS) + len(LOSSES)}")
    print(f"Estimated total time: ~{(len(BANDWIDTHS) + len(DELAYS) + len(LOSSES)) * (DURATION + 10) / 60:.1f} minutes")
    # print(f"\nNote: Parking lot has TWO bottlenecks in series")
    # print(f"      - Bottleneck 1: s1 -> s2 (first hop)")
    # print(f"      - Bottleneck 2: s2 -> s3 (second hop)")
    print(f"{'='*70}")
    
    try:
        # Run experiment sets
        run_varying_bandwidth()
        run_varying_delay()
        run_varying_loss()
        
        # Print summary
        # print_summary_statistics()
        
        # Record end time
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n{'='*70}")
        print(f"ALL EXPERIMENTS COMPLETED")
        print(f"{'='*70}")
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print(f"Results saved in: {RESULTS_DIR}/")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\nExperiments interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()