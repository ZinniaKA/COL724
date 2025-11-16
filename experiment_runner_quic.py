#!/usr/bin/env python3
"""
QUIC Experiment Runner for Mininet
Runs QUIC throughput tests across different network topologies
"""

import argparse
import os
import sys
from mininet.net import Mininet
from mininet.node import Host, OVSBridge
from mininet.link import TCLink
from mininet.log import setLogLevel, info
import helper_quic


def main():
    parser = argparse.ArgumentParser(description="Run QUIC experiments in Mininet")
    parser.add_argument(
        "--topo", 
        required=True, 
        help="Topology name (dumbbell, parkinglot, multibottleneck)"
    )
    parser.add_argument(
        "--bw", 
        type=int, 
        default=30, 
        help="Bottleneck bandwidth in Mbps"
    )
    parser.add_argument(
        "--delay", 
        default="2ms", 
        help="Link delay"
    )
    parser.add_argument(
        "--loss", 
        type=float, 
        default=0, 
        help="Packet loss percentage"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=10, 
        help="Duration of each flow in seconds"
    )
    parser.add_argument(
        "--hosts", 
        type=int, 
        default=40, 
        help="Total number of hosts"
    )
    
    args = parser.parse_args()
    
    # Get absolute paths to QUIC scripts
    script_dir = os.path.dirname(os.path.abspath(__file__))
    quic_server_script = os.path.join(script_dir, "quic_server.py")
    quic_client_script = os.path.join(script_dir, "quic_client.py")
    
    # Verify scripts exist
    if not os.path.exists(quic_server_script):
        info(f"ERROR: QUIC server script not found: {quic_server_script}\n")
        sys.exit(1)
    if not os.path.exists(quic_client_script):
        info(f"ERROR: QUIC client script not found: {quic_client_script}\n")
        sys.exit(1)
    
    # Load topology
    info(f"*** Loading topology: {args.topo}\n")
    topo = helper_quic.load_topology(
        args.topo, 
        args.bw, 
        args.delay, 
        args.loss, 
        args.hosts
    )
    
    # Create Mininet network
    info("*** Creating network\n")
    net = Mininet(
        topo=topo, 
        host=Host, 
        link=TCLink, 
        switch=OVSBridge, 
        controller=None
    )
    
    # Start network
    info("*** Starting network\n")
    net.start()
    
    # Get switch interfaces to monitor
    switch_throughput_node = topo.switch_interface(net)
    
    info("*** Experiment Started ^-^ \n")
    info(f"*** Configuration: bw={args.bw}Mbps, delay={args.delay}, loss={args.loss}%, duration={args.duration}s\n")
    
    # Get all hosts
    hosts = []
    for i in range(args.hosts):
        hosts.append(net.get(f"h{i}"))
    
    # Run QUIC experiments
    try:
        if args.topo == "multibottleneck":
            # Multibottleneck topology has additional interfaces to monitor
            other_throughput_node = topo.other_interfaces(net)
            results = helper_quic.run_quic_experiments(
                hosts, 
                args.hosts, 
                switch_throughput_node, 
                args.duration,
                quic_server_script,
                quic_client_script,
                other_throughput_node
            )
        else:
            results = helper_quic.run_quic_experiments(
                hosts, 
                args.hosts, 
                switch_throughput_node, 
                args.duration,
                quic_server_script,
                quic_client_script
            )
        
        # Print summary
        info("\n*** Experiment Summary ***\n")
        info(f"Topology: {args.topo}\n")
        info(f"Total throughput: {sum(results['tx_throughput']):.2f} Mbps\n")
        info(f"Results saved to results/ directory\n")
        
    except Exception as e:
        info(f"*** ERROR during experiment: {e}\n")
        import traceback
        traceback.print_exc()
    
    # Stop network
    info("*** Stopping network\n")
    net.stop()
    
    info("*** Experiment Completed :) ***\n")


if __name__ == "__main__":
    setLogLevel("info")
    main()