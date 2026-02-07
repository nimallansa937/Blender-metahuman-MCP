"""
Thread-safe command execution for Blender.

Blender's Python API (bpy) can only be called from the main thread.
This module provides a queue-based system where:
  1. TCP server thread puts commands into a queue
  2. A bpy.app.timers callback on the main thread polls the queue
  3. Commands execute on the main thread and results are stored
  4. The TCP thread retrieves results via a thread-safe dict
"""

import queue
import threading
import uuid
import time
import traceback


class CommandQueue:
    """Thread-safe command queue for bridging TCP thread <-> Blender main thread."""

    def __init__(self):
        self._command_queue = queue.Queue()
        self._results = {}
        self._results_lock = threading.Lock()
        self._timer_registered = False

    def submit_command(self, handler_func, params):
        """Submit a command for execution on the main thread.

        Args:
            handler_func: Callable that takes (params) and returns a result dict.
            params: Dict of parameters to pass to the handler.

        Returns:
            str: Unique command ID to retrieve the result later.
        """
        command_id = str(uuid.uuid4())
        self._command_queue.put((command_id, handler_func, params))
        return command_id

    def get_result(self, command_id, timeout=10.0):
        """Wait for and retrieve the result of a submitted command.

        Args:
            command_id: The ID returned by submit_command.
            timeout: Max seconds to wait for the result.

        Returns:
            dict: The result from the handler, or an error dict on timeout.
        """
        start = time.time()
        while time.time() - start < timeout:
            with self._results_lock:
                if command_id in self._results:
                    return self._results.pop(command_id)
            time.sleep(0.01)
        return {"status": "error", "error": f"Command timed out after {timeout}s"}

    def _process_queue(self):
        """Process pending commands. Called by bpy.app.timers on the main thread."""
        try:
            while not self._command_queue.empty():
                try:
                    command_id, handler_func, params = self._command_queue.get_nowait()
                except queue.Empty:
                    break

                try:
                    result = handler_func(params)
                    if not isinstance(result, dict):
                        result = {"status": "success", "result": result}
                except Exception as e:
                    result = {
                        "status": "error",
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }

                with self._results_lock:
                    self._results[command_id] = result
        except Exception:
            pass  # Don't crash the timer

        return 0.05  # Re-run every 50ms

    def start_timer(self):
        """Register the bpy.app.timers callback. Must be called from main thread."""
        if not self._timer_registered:
            import bpy
            bpy.app.timers.register(self._process_queue, persistent=True)
            self._timer_registered = True

    def stop_timer(self):
        """Unregister the timer callback."""
        if self._timer_registered:
            import bpy
            try:
                bpy.app.timers.unregister(self._process_queue)
            except Exception:
                pass
            self._timer_registered = False


# Global singleton
command_queue = CommandQueue()
