"""
Helper functions for QUIC experiments in Mininet
"""

import importlib
import os
import time
from mininet.log import info


def get_bytes(device):
    """Get transmitted bytes for a network device"""
    tx = int(open(f"/sys/class/net/{device}/statistics/tx_bytes").read())
    return tx


def get_rx_bytes(device):
    """Get received bytes for a network device"""
    rx = int(open(f"/sys/class/net/{device}/statistics/rx_bytes").read())
    return rx


def generate_certificates(host):
    """
    Generate self-signed certificates for QUIC/TLS
    
    Args:
        host: Mininet host to generate certificates on
    """
    info(f"*** Generating certificates on {host.name}\n")
    
    # Create directory for certificates
    host.cmd("mkdir -p /tmp/certs")
    
    # Generate private key and self-signed certificate
    host.cmd(
        "openssl req -new -x509 -days 1 -nodes "
        "-out /tmp/certs/cert.pem -keyout /tmp/certs/key.pem "
        "-subj '/CN=localhost' > /dev/null 2>&1"
    )


def run_quic_experiments(hosts, number_of_hosts, switch_interface, duration, 
                         quic_server_script, quic_client_script, other_switch=None):
    """
    Run QUIC throughput experiments
    
    Args:
        hosts: List of Mininet hosts
        number_of_hosts: Total number of hosts
        switch_interface: List of switch interfaces to monitor
        duration: Duration of each flow in seconds
        quic_server_script: Path to QUIC server script
        quic_client_script: Path to QUIC client script
        other_switch: Optional list of other switch interfaces to monitor
    """
    switches_count = len(switch_interface)
    t0 = time.time()
    tx1, tx2, tx_throughput = [], [], []
    rx1, rx2, rx_throughput = [], [], []
    
    # Record initial byte counts
    for i in range(switches_count):
        tx1.append(get_bytes(switch_interface[i]))
    
    if other_switch is not None:
        for i in range(len(other_switch)):
            rx1.append(get_rx_bytes(other_switch[i]))
    
    # Split hosts into sources and destinations
    mid = number_of_hosts // 2
    s1_hosts = hosts[:mid]
    s2_hosts = hosts[mid:]
    
    info(f"*** Running QUIC between {len(s1_hosts)} sources and {len(s2_hosts)} destinations\n")
    
    # Generate certificates on all destination hosts
    for h in s2_hosts:
        generate_certificates(h)
    
    # Start QUIC servers on destination hosts
    info("*** Starting QUIC servers\n")
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
    info("*** QUIC servers started\n")
    
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Start QUIC clients on source hosts
    info("*** Starting QUIC clients\n")
    for i in range(mid):
        source = s1_hosts[i]
        dest = s2_hosts[i]
        
        output_file = f"results/{t0}_quic_{source.name}_to_{dest.name}.json"
        
        source.cmd(
            f"python3 {quic_client_script} "
            f"--host {dest.IP()} --port 4433 "
            f"--duration {duration} "
            f"--output {output_file} "
            f"--no-verify "
            f"--log-level WARNING "
            f"> /tmp/{source.name}_client.log 2>&1 &"
        )
    
    info(f"*** QUIC clients started, running for {duration} seconds\n")
    
    # Wait for experiments to complete
    time.sleep(duration + 4)
    
    # Record final byte counts and calculate throughput
    info("*** Calculating throughput\n")
    for i in range(switches_count):
        tx2.append(get_bytes(switch_interface[i]))
        throughput = ((tx2[i] - tx1[i]) * 8) / 1e6 / duration
        tx_throughput.append(throughput)
        info(f"*** Switch {switch_interface[i]}: Tx_throughput = {throughput:.2f} Mbps\n")
    
    if other_switch is not None:
        for i in range(len(other_switch)):
            rx2.append(get_rx_bytes(other_switch[i]))
            throughput = ((rx2[i] - rx1[i]) * 8) / 1e6 / duration
            rx_throughput.append(throughput)
            info(f"*** Switch {other_switch[i]}: Rx_throughput = {throughput:.2f} Mbps\n")
    
    # Stop servers
    info("*** Stopping QUIC servers\n")
    for h in s2_hosts:
        h.cmd("pkill -f quic_server.py")
    
    # Cleanup
    for h in hosts:
        h.cmd("pkill -f quic_client.py")
    
    return {
        "tx_throughput": tx_throughput,
        "rx_throughput": rx_throughput if other_switch else None,
        "interfaces": switch_interface,
        "duration": duration,
    }


def load_topology(topo_name, bw, delay, loss, number_of_hosts):
    """
    Load network topology
    
    Args:
        topo_name: Name of topology (dumbbell, parkinglot, multibottleneck)
        bw: Bandwidth in Mbps
        delay: Link delay
        loss: Packet loss percentage
        number_of_hosts: Total number of hosts
    
    Returns:
        Topology object
    """
    intermediate_switch_bw = 0.8 * bw
    low_intermediate_switch_bw = 0.6 * bw
    
    # Import topology module
    module = importlib.import_module(topo_name)
    
    # Find topology class
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, type):
            if topo_name == "dumbbell":
                return obj(bw=bw, delay=delay, loss=loss)
            elif topo_name == "parkinglot":
                return obj(
                    bw1=bw, 
                    bw2=intermediate_switch_bw, 
                    delay=delay, 
                    loss=loss, 
                    number_of_hosts=number_of_hosts
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