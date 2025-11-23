#!/usr/bin/env python3
"""
QUIC Experiment Runner for Mininet
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
    """Main experiment runner"""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Run QUIC throughput experiments in Mininet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--topo", 
        required=True, 
        choices=['dumbbell', 'parkinglot', 'multibottleneck'],
        help="Network topology to use"
    )
    parser.add_argument(
        "--bw", 
        type=int, 
        default=15, 
        help="Bottleneck bandwidth in Mbps (default: 15)"
    )
    parser.add_argument(
        "--delay", 
        default="2ms", 
        help="Link delay (default: 2ms)"
    )
    parser.add_argument(
        "--loss", 
        type=float, 
        default=2, 
        help="Packet loss percentage 0-100 (default: 2)"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=60, 
        help="Duration of experiment in seconds (default: 60)"
    )
    parser.add_argument(
        "--hosts", 
        type=int, 
        default=40, 
        help="Total number of hosts (default: 40)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for results (auto-generated if not specified)"
    )
    
    args = parser.parse_args()
    
    # Auto-generate output directory name if not provided
    if args.output_dir is None:
        # Format: dumbbell_bw15_delay2ms_loss2
        output_dir = f"{args.topo}_bw{args.bw}_delay{args.delay}_loss{int(args.loss)}"
    else:
        output_dir = args.output_dir
    
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
    # info("Creating network\n")
    net = Mininet(
        topo=topo, 
        host=Host, 
        link=TCLink, 
        switch=OVSBridge, 
        controller=None   # No controller needed for simple forwarding
    )
    
    # Start network
    info("*** Starting network\n")
    net.start()
    
    # Get switch interfaces to monitor
    switch_throughput_node = topo.switch_interface(net)

    # Print experiment configuration
    info("=" * 70 + "\n")
    info(" QUIC Throughput Experiment Started\n")
    info("=" * 70 + "\n")
    # info(f"Topology:       {args.topo}\n")
    # info(f"Bandwidth:      {args.bw} Mbps\n")
    # info(f"Delay:          {args.delay}\n")
    # info(f"Loss:           {args.loss}%\n")
    # info(f"Duration:       {args.duration}s\n")
    # info(f"Hosts:          {args.hosts}\n")
    # info(f"Flows:          {args.hosts // 2}\n")
    # info(f"Output dir:     {output_dir}/\n")
    # info("=" * 70 + "\n")

    # info("*** Experiment Started ^-^ \n")
    # info(f"*** Configuration: bw={args.bw}Mbps, delay={args.delay}, loss={args.loss}%, duration={args.duration}s\n")
    # info(f"*** Output directory: {output_dir}\n")
    
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
                output_dir,
                other_throughput_node,
                args.bw,
            )
        else:
            results = helper_quic.run_quic_experiments(
                hosts, 
                args.hosts, 
                switch_throughput_node, 
                args.duration,
                quic_server_script,
                quic_client_script,
                output_dir,
                bandwidth=args.bw #fix
            )
        
        # Print summary
        info("\n")
        info("=" * 70 + "\n")
        # info(" Experiment Summary\n")
        # info("=" * 70 + "\n")
        # info(f"Topology:          {args.topo}\n")
        # info(f"Total throughput:  {sum(results.values()):.2f} Mbps\n")
        # # info(f"Results saved to:  {output_dir}/\n")
        # info("=" * 70 + "\n")        

    except KeyboardInterrupt:
        info("\n*** Experiment interrupted by user\n")
    except Exception as e:
        info(f"\n*** ERROR during experiment: {e}\n")
        import traceback
        traceback.print_exc()
    
    # Stop network
    info("*** Stopping network\n")
    net.stop()
    
    info("*** Experiment Completed\n")


if __name__ == "__main__":
    setLogLevel("info")
    main()