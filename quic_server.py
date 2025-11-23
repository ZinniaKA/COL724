#!/usr/bin/env python3
"""
QUIC Server
"""

import argparse
import asyncio
import logging
import time
from collections import defaultdict

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived, ConnectionTerminated


class ThroughputServerProtocol(QuicConnectionProtocol):
    """QUIC protocol handler for throughput testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bytes_received = defaultdict(int)
        self.start_time = time.time()
        
    # def quic_event_received(self, event: QuicEvent) -> None:
    #     """Handle QUIC events"""
    #     if isinstance(event, StreamDataReceived):
    #         # Track bytes received per stream
    #         self.bytes_received[event.stream_id] += len(event.data)
            
    #         # If stream is finished, log throughput
    #         if event.end_stream:
    #             elapsed = time.time() - self.start_time
    #             total_bytes = self.bytes_received[event.stream_id]
    #             throughput_mbps = (total_bytes * 8) / (elapsed * 1e6)
    #             logging.info(
    #                 f"Stream {event.stream_id}: "
    #                 f"Received {total_bytes} bytes in {elapsed:.2f}s "
    #                 f"({throughput_mbps:.2f} Mbps)"
    #             )
                
    #     elif isinstance(event, ConnectionTerminated):
    #         # Log total connection stats
    #         elapsed = time.time() - self.start_time
    #         total_bytes = sum(self.bytes_received.values())
    #         throughput_mbps = (total_bytes * 8) / (elapsed * 1e6) if elapsed > 0 else 0
    #         logging.info(
    #             f"Connection closed: "
    #             f"Total {total_bytes} bytes in {elapsed:.2f}s "
    #             f"({throughput_mbps:.2f} Mbps)"
    #         )


async def main(host: str, port: int, cert_file: str, key_file: str):
    """Start QUIC server"""
    
    # Configure QUIC
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=["throughput-test"],
    )
    
    # Load TLS certificate and key
    configuration.load_cert_chain(cert_file, key_file)
    
    # Start server
    # logging.info(f"Starting QUIC server on {host}:{port}")
    
    await serve(
        host,
        port,
        configuration=configuration,
        create_protocol=ThroughputServerProtocol,
    )
    
    # Keep server running
    await asyncio.Future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QUIC throughput server")
    parser.add_argument("--host", type=str, default="::", help="Host to bind to")
    parser.add_argument("--port", type=int, default=4433, help="Port to bind to")
    parser.add_argument("--cert", type=str, default="cert.pem", help="TLS certificate file")
    parser.add_argument("--key", type=str, default="key.pem", help="TLS key file")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Configure logging
    # logging.basicConfig(
    #     format="%(asctime)s %(levelname)s %(message)s",
    #     level=getattr(logging, args.log_level.upper()),
    # )
    
    try:
        asyncio.run(main(args.host, args.port, args.cert, args.key))
    except KeyboardInterrupt:
        logging.info("Server stopped by user")