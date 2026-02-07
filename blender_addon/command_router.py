"""
Command router — dispatches JSON commands to the appropriate handler.

Maps command name strings to handler functions and executes them
on Blender's main thread via the CommandQueue.
"""

import logging
from .utils.thread_safe import command_queue

logger = logging.getLogger("blender_metahuman_mcp.command_router")


class CommandRouter:
    """Routes incoming JSON commands to registered handler functions."""

    def __init__(self):
        self._handlers = {}

    def register(self, command_name, handler_func):
        """Register a handler function for a command name.

        Args:
            command_name: String command identifier (e.g., "move_bone").
            handler_func: Callable(params: dict) -> dict.
        """
        self._handlers[command_name] = handler_func
        logger.debug(f"Registered handler for '{command_name}'")

    def register_many(self, handlers_dict):
        """Register multiple handlers at once.

        Args:
            handlers_dict: Dict mapping command_name -> handler_func.
        """
        for name, func in handlers_dict.items():
            self.register(name, func)

    def dispatch(self, command_name, params):
        """Dispatch a command to its handler, executing on Blender's main thread.

        Args:
            command_name: The command to execute.
            params: Dict of parameters.

        Returns:
            dict with 'status' and 'result' or 'error'.
        """
        handler = self._handlers.get(command_name)
        if not handler:
            available = ", ".join(sorted(self._handlers.keys()))
            return {
                "status": "error",
                "error": f"Unknown command: '{command_name}'. Available: {available}"
            }

        # Submit to the command queue for main-thread execution
        command_id = command_queue.submit_command(handler, params)
        result = command_queue.get_result(command_id, timeout=15.0)
        return result

    def list_commands(self):
        """Return a list of all registered command names."""
        return sorted(self._handlers.keys())
