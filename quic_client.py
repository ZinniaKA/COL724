#!/usr/bin/env python3
"""
QUIC Client
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
    """QUIC client protocol handler"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bytes_sent = 0
        self.start_time = None
        self.metrics_buffer = []  # Buffer metrics in memory to avoid blocking I/O - ow high delay

    # def quic_event_received(self, event: QuicEvent) -> None:
    #     """Handle QUIC events (required by protocol)"""
    #     pass


async def send_data_with_metrics(
    client: ThroughputClientProtocol,
    duration: int,
    stream_id: int,  # QUIC stream ID
    metrics_file: str,
    chunk_size: int = 16384,  # Reduced from 65536 to 16KB for better loss handling - not much effect
    target_rate_mbps: Optional[float] = None 
) -> dict:
    """
    Send data for specified duration and collect metrics per second
    """

    # Prepare data chunk
    data_chunk = b"x" * chunk_size
    bytes_sent = 0

    start_time = time.time()
    end_time = start_time + duration
    
    # Calculate sleep time based on target rate or use default
    if target_rate_mbps:
        target_bytes_per_sec = (target_rate_mbps * 1_000_000) / 8         # Mbps to bytes per second
        # Calculate time between chunks to achieve target rate
        sleep_time = chunk_size / target_bytes_per_sec
        # logging.info(f"Rate pacing: {target_rate_mbps:.2f} Mbps target (sleep {sleep_time*1000:.2f}ms per chunk)")    
        
    else:
        target_bytes_per_sec = (15 * 1_000_000) / 8  # 15 Mbps per client
        sleep_time = chunk_size / target_bytes_per_sec
        # logging.info(f"Default pacing: 12 Mbps target (sleep {sleep_time*1000:.2f}ms per chunk)")
    
    # Metrics tracking variables (per second)
    last_log_time = start_time
    last_bytes = 0
    
    # logging.info(f"Starting transmission: duration={duration}s, chunk_size={chunk_size}B")

    # Main transmission loop   
    while time.time() < end_time:
        current_time = time.time()
        send_start = time.time()

        # Send data chunk to QUIC stream
        client._quic.send_stream_data(stream_id, data_chunk, end_stream=False)
        bytes_sent += chunk_size
        
        # Transmit queued packets to network
        client.transmit()
        
        # Collect metrics every second (store in memory, no file I/O during transmission)        
        if current_time - last_log_time >= 1.0:
            elapsed = int(current_time - start_time)
            
            # Extract RTT from QUIC connection (in ms)
            try:
                rtt_ms = client._quic._loss._rtt_smoothed * 1000
            except (AttributeError, TypeError): #added error types
                rtt_ms = 0
            
            # Extract congestion window from QUIC connection (in bytes)
            # try:
            #     cwnd_bytes = client._quic._loss._congestion_window
            # except (AttributeError, TypeError): #added error types
            #     cwnd_bytes = 0
            
            # Calculate bytes sent in this second
            bytes_this_second = bytes_sent - last_bytes
            
            # Write to shared metrics file (one line per client per second)
            metric = {
                'time': elapsed,
                'rtt_ms': round(rtt_ms, 2),
                # 'cwnd_bytes': int(cwnd_bytes),
                # 'bytes_sent': bytes_this_second
            }
            
            # Store metric in memory buffer (no disk I/O - prevents blocking)
            client.metrics_buffer.append(metric)

            # try:
            #     with open(metrics_file, 'a') as f:
            #         f.write(json.dumps(metric) + '\n')
            # except Exception as e:
            #     logging.warning(f"Failed to write metrics: {e}")
            
            last_log_time = current_time
            last_bytes = bytes_sent
        
        # Rate pacing: sleep to match target sending rate
        elapsed = time.time() - send_start
        sleep_duration = max(0, sleep_time - elapsed)
        await asyncio.sleep(sleep_duration)
    
    # Write all buffered metrics to file in one batch (after transmission completes)
    if metrics_file and client.metrics_buffer:
        try:
            with open(metrics_file, 'a') as f:
                for m in client.metrics_buffer:
                    f.write(json.dumps(m) + '\n')
            logging.info(f"Wrote {len(client.metrics_buffer)} metrics to file")
        except (IOError, OSError) as e:  # added exception types - general before
            logging.warning(f"Failed to write metrics: {e}")

    # Send final chunk with end_stream flag to close stream
    client._quic.send_stream_data(stream_id, b"", end_stream=True)
    client.transmit()
    
    # Calculate final statistics
    actual_duration = time.time() - start_time
    throughput_mbps = (bytes_sent * 8) / (actual_duration * 1e6)
    
    stats = {
        "bytes_sent": bytes_sent,
        "duration": actual_duration,
        "throughput_mbps": throughput_mbps,
    }
    
    # logging.info(f"Transmission complete: {bytes_sent} bytes in {actual_duration:.2f}s ({throughput_mbps:.2f} Mbps)")
        
    return stats


async def run_client(
    host: str,
    port: int,
    duration: int,
    metrics_file: str,
    verify_mode: int = 0,  # TLS verification mode (0=no verify, 2=verify)
    chunk_size: int = 16384,
    target_rate_mbps: Optional[float] = None 
) -> dict:
    """Run QUIC client     """
    
    # Configure QUIC connection
    configuration = QuicConfiguration(
        is_client=True,
        alpn_protocols=["throughput-test"],
        verify_mode=verify_mode,
        max_datagram_frame_size=1200,  # Stay below MTU to avoid IP fragmentation
    )
    
    # logging.info(f"Connecting to {host}:{port}")
    
    # Establish QUIC connection
    async with connect(
        host,
        port,
        configuration=configuration,
        create_protocol=ThroughputClientProtocol,
    ) as client:
        # logging.info("Connected successfully")
        
        # Get QUIC stream ID and start data transmission
        stream_id = client._quic.get_next_available_stream_id()
        stats = await send_data_with_metrics(
            client, 
            duration, 
            stream_id, 
            metrics_file,
            chunk_size=chunk_size,
            target_rate_mbps=target_rate_mbps)
        
        stats["server"] = f"{host}:{port}"
        stats["protocol"] = "QUIC"
        
        # Brief delay to allow final packets to be processed
        await asyncio.sleep(0.5)
        
        return stats


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="QUIC throughput testing client",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--host", type=str, required=True, help="Server IP address")
    parser.add_argument("--port", type=int, default=4433, help="Server port (default: 4433)")
    parser.add_argument("--duration", type=int, default=10, help="Test duration in seconds (default: 10)")
    parser.add_argument("--metrics-file", type=str, required=True, help="Path to metrics output file (JSON)/ Shared metrics file")
    parser.add_argument("--log-level", type=str, default="WARNING",choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Logging level (default: WARNING)")
    parser.add_argument("--no-verify", action="store_true", help="Disable TLS certificate verification")
    parser.add_argument("--chunk-size", type=int, default=16384, help="Chunk size in bytes (default: 16384)")
    parser.add_argument("--rate", type=float, default=None, help="Target rate in Mbps for pacing (default: auto)")
    
    args = parser.parse_args()
    
    # Configure logging with clean format
    # logging.basicConfig(
    #     format="%%(levelname)s %(message)s",
    #     level=getattr(logging, args.log_level.upper()),
    # ) # need to update (asctime)s 
    
    # Set TLS verification mode
    verify_mode = 0 if args.no_verify else 2
    
    # Run the client
    try:
        stats = asyncio.run(run_client(
            args.host,
            args.port,
            args.duration,
            args.metrics_file,
            verify_mode,
            chunk_size=args.chunk_size,
            target_rate_mbps=args.rate
        ))

        # Print summary (only if INFO level or higher)
        # if logging.getLogger().isEnabledFor(logging.INFO):
        #     print(f"Test complete: {stats['throughput_mbps']:.2f} Mbps over {stats['duration']:.2f}s")
        
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
        exit(130)
    except Exception as e:
        logging.error(f"Client error: {e}") # , exc_info=True)
        exit(1)