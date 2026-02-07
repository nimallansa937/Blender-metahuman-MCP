"""
Threaded TCP server that runs inside Blender.

Listens for JSON commands from the MCP server process,
dispatches them through the command router (on the main thread),
and returns JSON responses.

Protocol: Newline-delimited JSON (each message terminated by \n)
"""

import socket
import threading
import json
import logging

logger = logging.getLogger("blender_metahuman_mcp.tcp_server")


class MCPTCPServer:
    """TCP server that bridges the MCP server process to Blender."""

    def __init__(self, host="127.0.0.1", port=9876, command_router=None):
        self.host = host
        self.port = port
        self.command_router = command_router
        self._server_socket = None
        self._thread = None
        self._running = False

    def start(self):
        """Start the TCP server in a daemon thread."""
        if self._running:
            logger.warning("TCP server is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        logger.info(f"MCP TCP server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the TCP server."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("MCP TCP server stopped")

    def _run_server(self):
        """Main server loop — accepts connections and handles them."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.settimeout(1.0)  # Allow periodic check of _running
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            logger.info(f"Listening on {self.host}:{self.port}")

            while self._running:
                try:
                    client_socket, addr = self._server_socket.accept()
                    logger.info(f"Connection from {addr}")
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue  # Check _running flag
                except OSError:
                    if self._running:
                        logger.error("Socket error in accept loop")
                    break

        except Exception as e:
            logger.error(f"TCP server error: {e}")
        finally:
            if self._server_socket:
                try:
                    self._server_socket.close()
                except Exception:
                    pass

    def _handle_client(self, client_socket):
        """Handle a single client connection — read commands, send responses."""
        client_socket.settimeout(30.0)
        buffer = ""

        try:
            while self._running:
                try:
                    data = client_socket.recv(65536)
                    if not data:
                        break  # Client disconnected

                    buffer += data.decode("utf-8")

                    # Process complete messages (newline-delimited)
                    while "\n" in buffer:
                        message, buffer = buffer.split("\n", 1)
                        message = message.strip()
                        if not message:
                            continue

                        response = self._process_message(message)
                        response_bytes = (json.dumps(response) + "\n").encode("utf-8")
                        client_socket.sendall(response_bytes)

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    break

        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

    def _process_message(self, message):
        """Parse a JSON message and dispatch to the command router."""
        try:
            request = json.loads(message)
        except json.JSONDecodeError as e:
            return {
                "id": None,
                "status": "error",
                "error": f"Invalid JSON: {e}"
            }

        request_id = request.get("id")
        command = request.get("command")
        params = request.get("params", {})

        if not command:
            return {
                "id": request_id,
                "status": "error",
                "error": "Missing 'command' field"
            }

        if self.command_router:
            result = self.command_router.dispatch(command, params)
            result["id"] = request_id
            return result
        else:
            return {
                "id": request_id,
                "status": "error",
                "error": "No command router configured"
            }
