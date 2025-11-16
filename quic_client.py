#!/usr/bin/env python3
"""
QUIC Client for throughput testing
Sends data to QUIC server to measure throughput
"""

import argparse
import asyncio
import logging
import time
import json
from typing import Optional

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent


class ThroughputClientProtocol(QuicConnectionProtocol):
    """QUIC protocol handler for throughput testing client"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bytes_sent = 0
        self.start_time = None
        self.end_time = None
        
    def quic_event_received(self, event: QuicEvent) -> None:
        """Handle QUIC events"""
        pass


async def send_data(
    client: ThroughputClientProtocol,
    duration: int,
    stream_id: int,
    chunk_size: int = 65536
) -> dict:
    """
    Send data for specified duration
    
    Args:
        client: QUIC client protocol
        duration: Duration to send data (seconds)
        stream_id: QUIC stream ID to use
        chunk_size: Size of each data chunk to send
    
    Returns:
        Dictionary with throughput statistics
    """
    data_chunk = b"x" * chunk_size
    bytes_sent = 0
    start_time = time.time()
    end_time = start_time + duration
    
    logging.info(f"Starting data transmission for {duration} seconds")
    
    while time.time() < end_time:
        # Send data chunk
        client._quic.send_stream_data(stream_id, data_chunk, end_stream=False)
        bytes_sent += chunk_size
        
        # Transmit packets
        client.transmit()
        
        # Small delay to avoid overwhelming the network
        await asyncio.sleep(0.001)
    
    # Send final chunk with end_stream flag
    client._quic.send_stream_data(stream_id, b"", end_stream=True)
    client.transmit()
    
    actual_duration = time.time() - start_time
    throughput_mbps = (bytes_sent * 8) / (actual_duration * 1e6)
    
    stats = {
        "bytes_sent": bytes_sent,
        "duration": actual_duration,
        "throughput_mbps": throughput_mbps,
        "chunk_size": chunk_size,
    }
    
    logging.info(
        f"Sent {bytes_sent} bytes in {actual_duration:.2f}s "
        f"({throughput_mbps:.2f} Mbps)"
    )
    
    return stats


async def run_client(
    host: str,
    port: int,
    duration: int,
    output_file: Optional[str] = None,
    verify_mode: int = 0
) -> dict:
    """
    Run QUIC client throughput test
    
    Args:
        host: Server hostname/IP
        port: Server port
        duration: Test duration in seconds
        output_file: Optional JSON output file
        verify_mode: TLS verification mode (0 = no verification)
    
    Returns:
        Dictionary with test statistics
    """
    
    # Configure QUIC client
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=["throughput-test"],
        verify_mode=verify_mode,
    )
    
    # Connect to server
    logging.info(f"Connecting to {host}:{port}")
    
    async with connect(
        host,
        port,
        configuration=configuration,
        create_protocol=ThroughputClientProtocol,
    ) as client:
        logging.info("Connected successfully")
        
        # Create a stream and send data
        stream_id = client._quic.get_next_available_stream_id()
        
        # Run throughput test
        stats = await send_data(client, duration, stream_id)
        
        # Add connection info
        stats["server"] = f"{host}:{port}"
        stats["protocol"] = "QUIC"
        
        # Wait a bit for final packets to be acknowledged
        await asyncio.sleep(0.5)
        
        # Save results to file if specified
        if output_file:
            with open(output_file, "w") as f:
                json.dump(stats, f, indent=2)
            logging.info(f"Results saved to {output_file}")
        
        return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QUIC throughput client")
    parser.add_argument("--host", type=str, required=True, help="Server host")
    parser.add_argument("--port", type=int, default=4433, help="Server port")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds")
    parser.add_argument("--output", type=str, help="Output JSON file for results")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    parser.add_argument("--no-verify", action="store_true", help="Disable TLS verification")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        level=getattr(logging, args.log_level.upper()),
    )
    
    # Run client
    verify_mode = 0 if args.no_verify else 2
    
    try:
        stats = asyncio.run(run_client(
            args.host,
            args.port,
            args.duration,
            args.output,
            verify_mode
        ))
        
        print(f"\n{'='*60}")
        print(f"QUIC Throughput Test Results")
        print(f"{'='*60}")
        print(f"Server: {stats['server']}")
        print(f"Duration: {stats['duration']:.2f} seconds")
        print(f"Bytes Sent: {stats['bytes_sent']:,}")
        print(f"Throughput: {stats['throughput_mbps']:.2f} Mbps")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logging.error(f"Client error: {e}", exc_info=True)
        exit(1)