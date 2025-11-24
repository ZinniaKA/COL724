"""
Helper functions for QUIC experiments in Mininet
Handles experiment execution, metrics aggregation, and result collection
"""

import importlib
import os
import time
import json
import csv
from collections import defaultdict
from mininet.log import info

# device: Network interface name (e.g., 's1-eth21')

def get_bytes(device):
    """Get transmitted bytes for a network device"""
    tx = int(open(f"/sys/class/net/{device}/statistics/tx_bytes").read())
    return tx

def get_rx_bytes(device):
    """Get received bytes for a network device"""
    rx = int(open(f"/sys/class/net/{device}/statistics/rx_bytes").read())
    return rx

def generate_certificates(host):
    """Generate self-signed TLS certificates for QUIC on a Mininet host object"""
    
    # info(f"*** Generating certificates on {host.name}\n")
    
    # Create certificate directory
    host.cmd("mkdir -p /tmp/certs")

    # Generate self-signed certificate and private key
    host.cmd(
        "openssl req -new -x509 -days 1 -nodes "
        "-out /tmp/certs/cert.pem -keyout /tmp/certs/key.pem "
        "-subj '/CN=localhost' > /dev/null 2>&1"
    )

def aggregate_metrics(raw_metrics_file, output_dir, duration):
    """Aggregate per-client metrics into summary csv files (per-second averages) in rtt.csv and switches.csv"""
    
    metrics_by_time = defaultdict(lambda: {'rtt': [] ,'cwnd':[]})
    
    # Read and parse all metrics from JSON file
    try:
        with open(raw_metrics_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    t = data['time']
                    metrics_by_time[t]['rtt'].append(data['rtt_ms'])
                    metrics_by_time[t]['cwnd'].append(data['cwnd_bytes'])

                except (json.JSONDecodeError, KeyError):  #added exceptions - skip malformed lines
                    continue
    except FileNotFoundError:
        info("*** Warning: Metrics file not found\n")
        return
    except IOError as e:
        info(f"*** Warning: Could not read metrics file: {e}\n")
        return 

    # Aggregate and write CSV files
    timestamp = os.path.basename(raw_metrics_file).split('_')[0]
    
    # Write RTT CSV: average RTT per second
    rtt_file = os.path.join(output_dir, "rtt.csv")
    with open(rtt_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_sec', 'avg_rtt_ms'])
        for t in sorted(metrics_by_time.keys()):
            if metrics_by_time[t]['rtt']:
                avg_rtt = sum(metrics_by_time[t]['rtt']) / len(metrics_by_time[t]['rtt'])
                writer.writerow([t, round(avg_rtt, 2)])

    # Write cwnd CSV: average RTT per second
    cwnd_file = os.path.join(output_dir, "cwnd.csv")
    with open(cwnd_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_sec', 'window'])
        for t in sorted(metrics_by_time.keys()):
            if metrics_by_time[t]['cwnd']:
                avg_rtt = sum(metrics_by_time[t]['cwnd']) / len(metrics_by_time[t]['cwnd'])
                writer.writerow([t, int(avg_rtt)])

    # Write Bytes CSV: total bytes sent per second (across all clients)
    # bytes_file = os.path.join(output_dir, "bytes.csv")
    # with open(bytes_file, 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['time_sec', 'total_bytes_sent'])
    #     for t in sorted(metrics_by_time.keys()):
    #         if metrics_by_time[t]['bytes']:
    #             total_bytes = sum(metrics_by_time[t]['bytes'])
    #             writer.writerow([t, total_bytes])
    
    info(f"Metrics saved\n")


def save_switch_throughput(switch_throughput, output_dir, timestamp, duration):
    """Save switch interface throughput measurements to CSV"""
    
    switches_file = os.path.join(output_dir, "switches.csv")
    with open(switches_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['interface', 'throughput_mbps', 'duration_sec'])
        for interface, throughput in switch_throughput.items():
            writer.writerow([interface, round(throughput, 2), duration])
    
    info(f"Results saved to csv\n")


def run_quic_experiments(hosts, number_of_hosts, switch_interface, duration, 
                         quic_server_script, quic_client_script, output_dir, other_switch=None, bandwidth=15):
    """
    Run QUIC throughput experiments between source and destination hosts
    
    hosts: List of all Mininet hosts
    switch_interface: List of switch interfaces to monitor (TX)
    other_switch: Optional list of additional interfaces to monitor (RX)
    
    """

    switches_count = len(switch_interface)
    t0 = int(time.time())
    tx1, tx2 = [], []
    
    # Record initial byte counts for TX interfaces
    for i in range(switches_count):
        tx1.append(get_bytes(switch_interface[i]))
    
    # Record initial byte counts for RX interfaces (if any)
    rx1, rx2 = [], []
    if other_switch is not None:
        for i in range(len(other_switch)):
            rx1.append(get_rx_bytes(other_switch[i]))
    
    # Split hosts: first half are sources, second half are destinations
    mid = number_of_hosts // 2
    s1_hosts = hosts[:mid]  # Source hosts
    s2_hosts = hosts[mid:]  # Destination hosts
    
    info(f"Running QUIC between {len(s1_hosts)} sources and {len(s2_hosts)} destinations for {duration}s\n")
    
    # Generate TLS certificates on all destination hosts
    info("Generating certificates\n")
    for h in s2_hosts:
        generate_certificates(h)
    
    # Start QUIC servers on destination hosts
    info("Starting QUIC servers\n")
    for h in s2_hosts:
        h.cmd(
            f"python3 {quic_server_script} "
            f"--host {h.IP()} --port 4433 "
            f"--cert /tmp/certs/cert.pem --key /tmp/certs/key.pem "
            f"--log-level WARNING "
            f"> /tmp/{h.name}_server.log 2>&1 &"
        )
    
    # Wait for servers to start
    time.sleep(2)
    info("QUIC servers started\n")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Shared metrics file for all clients (will be aggregated later)
    raw_metrics_file = os.path.join(output_dir, f"{t0}_raw_metrics.json")
    
    # # Remove old metrics file if exists
    # if os.path.exists(raw_metrics_file):
    #     os.remove(raw_metrics_file)
    
    # # Calculate per-flow target rate
    # # Formula: (link_bandwidth / number_of_flows) × 0.8 (conservative factor)
    per_flow_rate = (bandwidth / len(s1_hosts)) # * 0.8
    
    # info(f"Starting {len(s1_hosts)} QUIC clients\n")
    
    
    # Start QUIC clients on source hosts
    info("Starting QUIC clients\n")
    for i in range(mid):
        source = s1_hosts[i]
        dest = s2_hosts[i]
        
        source.cmd(
            f"python3 {quic_client_script} "
            f"--host {dest.IP()} --port 4433 "
            f"--duration {duration} --rate {per_flow_rate} " 
            f"--metrics-file {raw_metrics_file} "
            f"--no-verify "
            f"--log-level WARNING "
            f"> /tmp/{source.name}_client.log 2>&1 &"
        )
    
    info(f"QUIC clients started\n")
    
    # Wait for experiments to complete (add 4s buffer for cleanup)
    time.sleep(duration + 4)
    
    # Record final byte counts and calculate throughput
    info("Calculating throughput :\n")
    switch_throughput = {}
    
    # Calculate throughput for TX interfaces
    for i in range(switches_count):
        tx2.append(get_bytes(switch_interface[i]))
        throughput = ((tx2[i] - tx1[i]) * 8) / 1e6 / duration
        switch_throughput[switch_interface[i]] = throughput
        info(f"Switch {switch_interface[i]}: {throughput:.2f} Mbps\n")
    
    # Calculate throughput for RX interfaces (if any)
    if other_switch is not None:
        for i in range(len(other_switch)):
            rx2.append(get_rx_bytes(other_switch[i]))
            throughput = ((rx2[i] - rx1[i]) * 8) / 1e6 / duration
            switch_throughput[other_switch[i]] = throughput
            info(f"Switch {other_switch[i]}: {throughput:.2f} Mbps\n")
    
    # Aggregate per-client metrics from all clients
    info("Aggregating metrics\n")
    aggregate_metrics(raw_metrics_file, output_dir, duration)
    
    # Save switch throughput to CSV
    save_switch_throughput(switch_throughput, output_dir, t0, duration)
    
    # Stop QUIC servers
    info("Stopping QUIC servers\n")
    for h in s2_hosts:
        h.cmd("pkill -f quic_server.py")
    
    # Cleanup clients
    for h in hosts:
        h.cmd("pkill -f quic_client.py")
    
    # Clean up raw metrics file
    try:
        os.remove(raw_metrics_file)
    except:
        pass
    
    return switch_throughput


def load_topology(topo_name, bw, delay, loss, number_of_hosts,jitter=None):
    """Load and instantiate network topology"""    
    # Calculate bandwidth for intermediate links (multi-hop topologies)
    intermediate_switch_bw = 0.8 * bw
    low_intermediate_switch_bw = 0.6 * bw
    
    # Try to import topology module from different locations
    module = None
    for module_path in [f"topologies.{topo_name}", topo_name]:
        try:
            module = importlib.import_module(module_path)
            break
        except ImportError:
            continue
    
    if module is None:
        raise ImportError(
            f"Could not import topology '{topo_name}'. "
            f"Make sure {topo_name}.py exists in current directory or topologies/ directory"
        )
    
    # Find topology class in module and instantiate with appropriate parameters
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, type):
            if topo_name == "dumbbell":
                return obj(bw=bw, delay=delay, loss=loss, number_of_hosts=number_of_hosts)
            elif topo_name == "parkinglot":
                return obj(
                    bw1=bw, 
                    bw2=intermediate_switch_bw, 
                    delay=delay, 
                    loss=loss, 
                    number_of_hosts=number_of_hosts,
                    jitter=jitter
                )
            elif topo_name == "multibottleneck":
                return obj(
                    bw1=bw, 
                    bw2=intermediate_switch_bw, 
                    bw3=low_intermediate_switch_bw, 
                    delay=delay, 
                    loss=loss, 
                    number_of_hosts=number_of_hosts
                )
    
    raise Exception(f"No valid topology class found in {topo_name}!\n")