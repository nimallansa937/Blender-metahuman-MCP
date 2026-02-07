"""
Tests for the BlenderConnection TCP client.

Uses a mock TCP server to test the connection layer
without needing Blender to be running.
"""

import sys
import os
import unittest
import socket
import threading
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.blender_connection import BlenderConnection


class MockBlenderServer:
    """A simple mock TCP server that mimics the Blender addon."""

    def __init__(self, port=19876):
        self.port = port
        self._server = None
        self._thread = None
        self._running = False
        self.received_commands = []
        self.response_override = None

    def start(self):
        self._running = True
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.settimeout(2.0)
        self._server.bind(("127.0.0.1", self.port))
        self._server.listen(5)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server:
            self._server.close()
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self):
        while self._running:
            try:
                client, addr = self._server.accept()
                self._handle_client(client)
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client):
        client.settimeout(5.0)
        try:
            data = client.recv(65536).decode("utf-8")
            if "\n" in data:
                message = data.split("\n")[0]
                request = json.loads(message)
                self.received_commands.append(request)

                if self.response_override:
                    response = self.response_override
                else:
                    response = {
                        "id": request.get("id"),
                        "status": "success",
                        "result": {"echo": request.get("command")}
                    }

                client.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except Exception:
            pass
        finally:
            client.close()


class TestBlenderConnection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_server = MockBlenderServer(port=19876)
        cls.mock_server.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.mock_server.stop()

    def setUp(self):
        self.conn = BlenderConnection(host="127.0.0.1", port=19876)
        self.mock_server = self.__class__.mock_server
        self.mock_server.received_commands.clear()
        self.mock_server.response_override = None

    def tearDown(self):
        self.conn.disconnect()

    def test_ping(self):
        result = self.conn.send_command("ping")
        self.assertEqual(result["status"], "success")

    def test_send_command(self):
        result = self.conn.send_command("move_bone", {"bone_name": "test", "axis": "X", "amount": 0.1})
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(self.mock_server.received_commands), 1)
        cmd = self.mock_server.received_commands[0]
        self.assertEqual(cmd["command"], "move_bone")
        self.assertEqual(cmd["params"]["bone_name"], "test")

    def test_connection_refused(self):
        bad_conn = BlenderConnection(host="127.0.0.1", port=19999)
        bad_conn._max_retries = 1
        bad_conn._retry_delay = 0.1
        result = bad_conn.send_command("ping")
        self.assertEqual(result["status"], "error")
        self.assertIn("Cannot connect", result["error"])

    def test_custom_response(self):
        self.mock_server.response_override = {
            "id": None,
            "status": "error",
            "error": "Bone not found"
        }
        result = self.conn.send_command("get_bone_transform", {"bone_name": "nonexistent"})
        self.assertEqual(result["status"], "error")
        self.assertIn("Bone not found", result["error"])


if __name__ == "__main__":
    unittest.main()
