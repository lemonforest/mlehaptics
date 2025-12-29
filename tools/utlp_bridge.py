#!/usr/bin/env python3
"""
UTLP Bridge Daemon - Virtual ESP-NOW for VICE Emulator Cluster

This daemon connects multiple VICE emulator instances and simulates
ESP-NOW's broadcast behavior. When one C64 sends a packet, all other
connected C64s receive it.

Usage:
    python utlp_bridge.py [--ports 6502,6503,6504]

Architecture:
    ┌─────────────────────────┐
    │    UTLP Bridge Daemon   │
    │                         │
    │  - Listens on TCP ports │
    │  - Broadcasts packets   │
    │  - Simulates ESP-NOW    │
    └───────────┬─────────────┘
          ┌─────┴─────┐
          │           │
    ┌─────▼─────┐ ┌───▼─────┐
    │  VICE #1  │ │ VICE #2 │
    │  :6502    │ │ :6503   │
    └───────────┘ └─────────┘

VICE Configuration:
    Start VICE with User Port connected to TCP:

    x64sc -rsuser -rsuserbaud 9600 -rsuserdev 2 \
          -rsuser1 localhost:6502 utlp_c64.prg

Protocol (UTLP Packet over Serial):
    [STX] [LEN] [PAYLOAD...] [CHECKSUM] [ETX]

    STX:      0x02 (Start of packet)
    LEN:      Payload length (1 byte, max 200)
    PAYLOAD:  UTLP beacon data (10 bytes for seismic chirp)
    CHECKSUM: XOR of all payload bytes
    ETX:      0x03 (End of packet)

Example:
    10-byte UTLP beacon becomes 14-byte serial frame:
    [02] [0A] [stratum] [burst] [timestamp...] [checksum] [03]

Author: Claude (Anthropic)
Date: December 2025
License: GPL v3
"""

import argparse
import logging
import select
import socket
import sys
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

# Protocol constants
STX = 0x02  # Start of packet
ETX = 0x03  # End of packet
MAX_PAYLOAD_LEN = 200

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('UTLP-Bridge')


@dataclass
class Client:
    """Represents a connected VICE instance."""
    socket: socket.socket
    address: tuple
    port: int
    rx_buffer: bytearray
    packets_rx: int = 0
    packets_tx: int = 0
    connected_at: float = 0.0


class UTLPBridge:
    """
    UTLP Bridge Daemon - Connects VICE instances for distributed time sync.

    Acts as a virtual broadcast medium: packets from one client are
    forwarded to all other connected clients.
    """

    def __init__(self, ports: List[int]):
        """
        Initialize bridge with listening ports.

        Args:
            ports: List of TCP ports to listen on (one per VICE instance)
        """
        self.ports = ports
        self.clients: Dict[int, Client] = {}
        self.server_sockets: Dict[int, socket.socket] = {}
        self.running = False
        self.lock = threading.Lock()

        # Statistics
        self.total_packets = 0
        self.start_time = 0.0

    def start(self):
        """Start the bridge daemon."""
        logger.info("=" * 60)
        logger.info("UTLP Bridge Daemon - Virtual ESP-NOW for C64")
        logger.info("=" * 60)
        logger.info(f"Listening on ports: {self.ports}")
        logger.info("Waiting for VICE instances to connect...")
        logger.info("")

        self.running = True
        self.start_time = time.time()

        # Create server socket for each port
        for port in self.ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('localhost', port))
                sock.listen(1)
                sock.setblocking(False)
                self.server_sockets[port] = sock
                logger.info(f"  Port {port}: Listening...")
            except OSError as e:
                logger.error(f"  Port {port}: Failed to bind - {e}")
                self.stop()
                return

        logger.info("")

        # Main event loop
        try:
            self._event_loop()
        except KeyboardInterrupt:
            logger.info("\nShutdown requested...")
        finally:
            self.stop()

    def stop(self):
        """Stop the bridge daemon and clean up."""
        self.running = False

        # Close client connections
        with self.lock:
            for client in self.clients.values():
                try:
                    client.socket.close()
                except:
                    pass
            self.clients.clear()

        # Close server sockets
        for sock in self.server_sockets.values():
            try:
                sock.close()
            except:
                pass
        self.server_sockets.clear()

        # Print statistics
        uptime = time.time() - self.start_time if self.start_time else 0
        logger.info("")
        logger.info("=" * 60)
        logger.info("Bridge Statistics:")
        logger.info(f"  Uptime:         {uptime:.1f} seconds")
        logger.info(f"  Total packets:  {self.total_packets}")
        logger.info("=" * 60)

    def _event_loop(self):
        """Main event loop using select() for non-blocking I/O."""
        while self.running:
            # Build list of sockets to monitor
            read_sockets = list(self.server_sockets.values())
            with self.lock:
                read_sockets.extend(c.socket for c in self.clients.values())

            # Wait for activity (100ms timeout for responsiveness)
            try:
                readable, _, _ = select.select(read_sockets, [], [], 0.1)
            except (ValueError, OSError):
                # Socket closed during select
                continue

            for sock in readable:
                # Check if it's a server socket (new connection)
                for port, server_sock in self.server_sockets.items():
                    if sock is server_sock:
                        self._accept_connection(port, server_sock)
                        break
                else:
                    # It's a client socket (incoming data)
                    self._handle_client_data(sock)

    def _accept_connection(self, port: int, server_sock: socket.socket):
        """Accept a new VICE connection."""
        try:
            client_sock, address = server_sock.accept()
            client_sock.setblocking(False)

            client = Client(
                socket=client_sock,
                address=address,
                port=port,
                rx_buffer=bytearray(),
                connected_at=time.time()
            )

            with self.lock:
                # Close existing client on this port
                if port in self.clients:
                    try:
                        self.clients[port].socket.close()
                    except:
                        pass
                    logger.warning(f"Port {port}: Replaced existing connection")

                self.clients[port] = client

            logger.info(f"Port {port}: VICE connected from {address}")
            self._log_status()

        except Exception as e:
            logger.error(f"Port {port}: Accept failed - {e}")

    def _handle_client_data(self, sock: socket.socket):
        """Handle incoming data from a VICE client."""
        # Find which client this socket belongs to
        client = None
        with self.lock:
            for c in self.clients.values():
                if c.socket is sock:
                    client = c
                    break

        if not client:
            return

        # Read available data
        try:
            data = sock.recv(1024)
            if not data:
                # Connection closed
                self._disconnect_client(client)
                return

            client.rx_buffer.extend(data)

            # Process complete packets
            self._process_rx_buffer(client)

        except (ConnectionResetError, BrokenPipeError):
            self._disconnect_client(client)
        except BlockingIOError:
            pass  # No data available
        except Exception as e:
            logger.error(f"Port {client.port}: Read error - {e}")
            self._disconnect_client(client)

    def _process_rx_buffer(self, client: Client):
        """Extract and process complete packets from receive buffer."""
        while True:
            # Look for STX
            try:
                stx_idx = client.rx_buffer.index(STX)
            except ValueError:
                # No STX found, clear buffer up to last byte
                if len(client.rx_buffer) > 1:
                    client.rx_buffer = client.rx_buffer[-1:]
                return

            # Discard bytes before STX
            if stx_idx > 0:
                client.rx_buffer = client.rx_buffer[stx_idx:]

            # Need at least 4 bytes: STX, LEN, 1+ payload, ETX
            if len(client.rx_buffer) < 4:
                return

            # Get length
            payload_len = client.rx_buffer[1]
            if payload_len > MAX_PAYLOAD_LEN:
                # Invalid length, skip this STX
                client.rx_buffer = client.rx_buffer[1:]
                continue

            # Check if we have complete packet
            packet_len = 2 + payload_len + 2  # STX + LEN + payload + checksum + ETX
            if len(client.rx_buffer) < packet_len:
                return

            # Extract packet
            packet = bytes(client.rx_buffer[:packet_len])
            client.rx_buffer = client.rx_buffer[packet_len:]

            # Verify ETX
            if packet[-1] != ETX:
                logger.warning(f"Port {client.port}: Invalid ETX, discarding")
                continue

            # Verify checksum
            payload = packet[2:-2]
            expected_checksum = packet[-2]
            actual_checksum = 0
            for b in payload:
                actual_checksum ^= b

            if actual_checksum != expected_checksum:
                logger.warning(f"Port {client.port}: Checksum mismatch")
                continue

            # Valid packet - broadcast to others
            client.packets_rx += 1
            self.total_packets += 1
            self._broadcast_packet(client, packet)

    def _broadcast_packet(self, sender: Client, packet: bytes):
        """Broadcast a packet to all clients except the sender."""
        payload = packet[2:-2]

        # Log packet details (UTLP beacon format)
        if len(payload) >= 2:
            stratum = payload[0]
            burst = payload[1] if len(payload) > 1 else 0
            logger.debug(f"Port {sender.port} → Broadcast: stratum={stratum}, burst={burst}")

        # Send to all other clients
        with self.lock:
            for port, client in self.clients.items():
                if client is sender:
                    continue

                try:
                    client.socket.send(packet)
                    client.packets_tx += 1
                except (ConnectionResetError, BrokenPipeError):
                    # Will be cleaned up on next read attempt
                    pass
                except Exception as e:
                    logger.error(f"Port {port}: Send failed - {e}")

    def _disconnect_client(self, client: Client):
        """Handle client disconnection."""
        logger.info(f"Port {client.port}: VICE disconnected")

        with self.lock:
            if client.port in self.clients:
                del self.clients[client.port]

        try:
            client.socket.close()
        except:
            pass

        self._log_status()

    def _log_status(self):
        """Log current connection status."""
        with self.lock:
            connected = len(self.clients)
            total = len(self.ports)

        if connected == 0:
            logger.info("Status: No VICE instances connected")
        elif connected == 1:
            logger.info("Status: 1 VICE instance connected (waiting for more...)")
        else:
            logger.info(f"Status: {connected}/{total} VICE instances connected - SYNC POSSIBLE!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='UTLP Bridge Daemon - Virtual ESP-NOW for VICE Emulator Cluster',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example:
    # Start bridge with default ports
    python utlp_bridge.py

    # Start bridge with custom ports
    python utlp_bridge.py --ports 6502,6503,6504,6505

Then start VICE instances:
    x64sc -rsuser -rsuserbaud 9600 -rsuserdev 2 -rsuser1 localhost:6502 utlp_c64.prg
    x64sc -rsuser -rsuserbaud 9600 -rsuserdev 2 -rsuser1 localhost:6503 utlp_c64.prg
'''
    )

    parser.add_argument(
        '--ports', '-p',
        default='6502,6503,6504',
        help='Comma-separated list of TCP ports (default: 6502,6503,6504)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Parse ports
    try:
        ports = [int(p.strip()) for p in args.ports.split(',')]
    except ValueError:
        logger.error(f"Invalid port list: {args.ports}")
        sys.exit(1)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Start bridge
    bridge = UTLPBridge(ports)
    bridge.start()


if __name__ == '__main__':
    main()
