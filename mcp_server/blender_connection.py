"""
TCP client for communicating with the Blender addon.

Sends JSON commands over TCP to the Blender addon's TCP server
and receives JSON responses.
"""

import socket
import json
import os
import time
import logging
import uuid

logger = logging.getLogger("blender_metahuman_mcp.connection")


class BlenderConnection:
    """TCP client that connects to the Blender MCP addon."""

    def __init__(self, host=None, port=None):
        self.host = host or os.environ.get("BLENDER_HOST", "127.0.0.1")
        self.port = int(port or os.environ.get("BLENDER_PORT", "9876"))
        self._socket = None
        self._timeout = 15.0
        self._max_retries = 3
        self._retry_delay = 1.0

    def connect(self):
        """Establish TCP connection to Blender."""
        if self._socket:
            self.disconnect()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self._timeout)
        self._socket.connect((self.host, self.port))
        logger.info(f"Connected to Blender at {self.host}:{self.port}")

    def disconnect(self):
        """Close the TCP connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def is_connected(self):
        """Check if connection is alive."""
        if not self._socket:
            return False
        try:
            # Peek to check if socket is still valid
            self._socket.settimeout(0.1)
            self._socket.recv(1, socket.MSG_PEEK)
            self._socket.settimeout(self._timeout)
            return True
        except socket.timeout:
            self._socket.settimeout(self._timeout)
            return True  # Timeout = no data but connected
        except Exception:
            self._socket = None
            return False

    def send_command(self, command, params=None):
        """Send a command to Blender and return the response.

        Args:
            command: Command string (e.g., "move_bone").
            params: Optional dict of parameters.

        Returns:
            dict: Response from Blender with 'status' and 'result'/'error'.
        """
        request = {
            "id": str(uuid.uuid4()),
            "command": command,
            "params": params or {}
        }

        for attempt in range(self._max_retries):
            try:
                if not self.is_connected():
                    self.connect()

                # Send newline-delimited JSON
                message = json.dumps(request) + "\n"
                self._socket.sendall(message.encode("utf-8"))

                # Receive response
                response_data = self._receive_response()
                response = json.loads(response_data)
                return response

            except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as e:
                logger.warning(f"Connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                self.disconnect()
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                else:
                    return {
                        "status": "error",
                        "error": f"Cannot connect to Blender at {self.host}:{self.port}. "
                                 f"Ensure Blender is running with the MCP addon enabled."
                    }

            except socket.timeout:
                logger.error("Command timed out")
                return {"status": "error", "error": "Command timed out waiting for Blender response"}

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
                return {"status": "error", "error": f"Invalid response from Blender: {e}"}

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.disconnect()
                return {"status": "error", "error": str(e)}

        return {"status": "error", "error": "Max retries exceeded"}

    def _receive_response(self):
        """Receive a complete newline-delimited JSON response."""
        buffer = ""
        while True:
            chunk = self._socket.recv(65536).decode("utf-8")
            if not chunk:
                raise ConnectionResetError("Connection closed by Blender")

            buffer += chunk

            # Check for complete message (newline terminated)
            if "\n" in buffer:
                message, _ = buffer.split("\n", 1)
                return message.strip()

    def ping(self):
        """Test the connection with a ping command.

        Returns:
            bool: True if Blender is responsive.
        """
        try:
            result = self.send_command("ping")
            return result.get("status") == "success"
        except Exception:
            return False


# Global singleton connection
_connection = None


def get_connection():
    """Get or create the global Blender connection."""
    global _connection
    if _connection is None:
        _connection = BlenderConnection()
    return _connection
