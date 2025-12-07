"""
Memphora MCP Server - Add persistent memory to AI assistants.

This package provides an MCP (Model Context Protocol) server that connects
Claude, Cursor, and other AI assistants to Memphora's memory API.
"""

__version__ = "0.1.1"
__author__ = "Memphora"

from .server import main
from .client import MemphoraClient

__all__ = ["main", "MemphoraClient"]
