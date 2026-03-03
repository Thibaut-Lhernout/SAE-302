"""
Server module for the SAE32 search application.

- Listens for TCP client connections.
- Delegates search requests to the search_engine module.
- Uses threads to handle multiple clients concurrently.
"""

from __future__ import annotations

import json
import socket
import threading
from typing import Tuple

import search_engine

# --- Named constants ---

SERVER_HOST: str = "127.0.0.1"
SERVER_PORT: int = 65432
BUFFER_SIZE: int = 4096
MAX_LISTEN: int = 5


def handle_client_connection(connection: socket.socket, address: Tuple[str, int]) -> None:
    """
    Handle a single client connection in a dedicated thread.

    Parameters
    ----------
    connection : socket.socket
        TCP socket connected to the client.
    address : tuple[str, int]
        Client (host, port) address.
    """
    print(f"[NEW CONNECTION] Connected to {address}")

    try:
        while True:
            data = connection.recv(BUFFER_SIZE)
            if not data:
                # Client closed the connection.
                break

            try:
                request = json.loads(data.decode("utf-8"))
                query = request.get("query", "")
                exts = request.get("extensions", [])
                regex = request.get("regex", False)

                print(f"[{address}] Searching: {query!r} in {exts} (regex={regex})")

                results = search_engine.process_search(query, exts, regex)

                # Always send a JSON list, even if no results.
                if results is None:
                    results = []

                response_json = json.dumps(results)
                connection.sendall(response_json.encode("utf-8"))

            except json.JSONDecodeError:
                print(f"[{address}] Invalid JSON payload.")
                break

            except Exception as error:
                print(f"[{address}] Error while processing request: {error}")
                break

    finally:
        connection.close()
        print(f"[DISCONNECTED] {address} closed.")


def start_server() -> None:
    """
    Start the main TCP server loop.

    The server listens on SERVER_HOST:SERVER_PORT and
    spawns a new thread for each incoming client connection.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(MAX_LISTEN)

        print(f"[STARTING] Server running on {SERVER_HOST}:{SERVER_PORT}")

        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(
                target=handle_client_connection,
                args=(conn, addr),
                daemon=True,
            )
            thread.start()

    except Exception as error:
        print(f"[CRITICAL ERROR] Server failed: {error}")

    finally:
        server_socket.close()
        print("[SHUTDOWN] Server socket closed.")


if __name__ == "__main__":
    start_server()
