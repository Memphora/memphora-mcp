"""
Memphora MCP Server - Main server implementation.

This server exposes Memphora's memory capabilities to MCP-compatible
AI assistants like Claude Desktop, Cursor, and Windsurf.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    ResourceTemplate,
    Prompt,
    PromptMessage,
    PromptArgument,
    GetPromptResult,
)
from pydantic import AnyUrl

from .client import MemphoraClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memphora-mcp")

# Create the MCP server
server = Server("memphora")

# Global client instance (initialized on startup)
_client: MemphoraClient | None = None


def get_client() -> MemphoraClient:
    """Get or create the Memphora client."""
    global _client
    if _client is None:
        _client = MemphoraClient()
    return _client


# ============================================
# TOOLS - Functions Claude can call
# ============================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Memphora tools."""
    return [
        Tool(
            name="memphora_search",
            description=(
                "Search your personal memories for relevant information. "
                "Use this when the user asks about something they may have mentioned before, "
                "their preferences, past experiences, or any personal information. "
                "Examples: 'What's my favorite food?', 'Where do I work?', 'What projects am I working on?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for in memories"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="memphora_store",
            description=(
                "Store important information about the user for future recall. "
                "Use this when the user shares personal details, preferences, facts about themselves, "
                "or explicitly asks you to remember something. "
                "Examples: 'I work at Google', 'My favorite color is blue', 'Remember that I'm allergic to peanuts'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember (should be a complete, self-contained fact)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category (e.g., 'preference', 'work', 'health', 'relationship')",
                        "enum": ["preference", "work", "health", "relationship", "hobby", "travel", "general"]
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="memphora_extract_conversation",
            description=(
                "Extract and store memories from a conversation. "
                "Use this to save important information from a longer discussion. "
                "The system will automatically identify and store relevant facts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation": {
                        "type": "array",
                        "description": "List of messages in the conversation",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["user", "assistant"]
                                },
                                "content": {
                                    "type": "string"
                                }
                            },
                            "required": ["role", "content"]
                        }
                    }
                },
                "required": ["conversation"]
            }
        ),
        Tool(
            name="memphora_list_memories",
            description=(
                "List all stored memories for the user. "
                "Use this to see what information has been remembered."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to return (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="memphora_delete",
            description=(
                "Delete a specific memory by its ID. "
                "Use this when the user wants to forget something or correct incorrect information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The ID of the memory to delete"
                    }
                },
                "required": ["memory_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls from Claude."""
    client = get_client()
    
    try:
        if name == "memphora_search":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            
            logger.info(f"Searching memories: query='{query}', limit={limit}")
            result = await client.search(query=query, limit=limit)
            
            if not result.memories:
                return [TextContent(
                    type="text",
                    text="No relevant memories found for this query."
                )]
            
            # Format memories for Claude
            memory_texts = []
            for i, mem in enumerate(result.memories, 1):
                similarity = f" (relevance: {mem.similarity:.0%})" if mem.similarity else ""
                memory_texts.append(f"{i}. {mem.content}{similarity}")
            
            return [TextContent(
                type="text",
                text=f"Found {len(result.memories)} relevant memories:\n\n" + "\n".join(memory_texts)
            )]
        
        elif name == "memphora_store":
            content = arguments.get("content", "")
            category = arguments.get("category", "general")
            
            if not content:
                return [TextContent(type="text", text="Error: No content provided to store.")]
            
            logger.info(f"Storing memory: content='{content[:50]}...', category={category}")
            result = await client.store(
                content=content,
                metadata={"category": category, "source": "mcp"}
            )
            
            return [TextContent(
                type="text",
                text=f"✓ Memory stored successfully! I'll remember: \"{content}\""
            )]
        
        elif name == "memphora_extract_conversation":
            conversation = arguments.get("conversation", [])
            
            if not conversation:
                return [TextContent(type="text", text="Error: No conversation provided.")]
            
            logger.info(f"Extracting from conversation: {len(conversation)} messages")
            result = await client.extract_conversation(conversation=conversation)
            
            memories_count = result.get("memories_extracted", 0)
            return [TextContent(
                type="text",
                text=f"✓ Extracted {memories_count} memories from the conversation."
            )]
        
        elif name == "memphora_list_memories":
            limit = arguments.get("limit", 20)
            
            logger.info(f"Listing memories: limit={limit}")
            memories = await client.get_memories(limit=limit)
            
            if not memories:
                return [TextContent(
                    type="text",
                    text="No memories stored yet."
                )]
            
            memory_texts = []
            for mem in memories:
                memory_texts.append(f"• [{mem.id[:8]}...] {mem.content}")
            
            return [TextContent(
                type="text",
                text=f"Stored memories ({len(memories)}):\n\n" + "\n".join(memory_texts)
            )]
        
        elif name == "memphora_delete":
            memory_id = arguments.get("memory_id", "")
            
            if not memory_id:
                return [TextContent(type="text", text="Error: No memory ID provided.")]
            
            logger.info(f"Deleting memory: id={memory_id}")
            await client.delete_memory(memory_id=memory_id)
            
            return [TextContent(
                type="text",
                text=f"✓ Memory deleted successfully."
            )]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# ============================================
# RESOURCES - Data Claude can read
# ============================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available Memphora resources."""
    user_id = os.getenv("MEMPHORA_USER_ID", "mcp_default_user")
    
    return [
        Resource(
            uri=AnyUrl(f"memphora://users/{user_id}/memories"),
            name="My Memories",
            description="All stored memories for the current user",
            mimeType="application/json"
        ),
        Resource(
            uri=AnyUrl(f"memphora://users/{user_id}/summary"),
            name="Memory Summary",
            description="Summary of stored memories and statistics",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read a Memphora resource."""
    import json
    
    client = get_client()
    uri_str = str(uri)
    
    try:
        if "/memories" in uri_str:
            memories = await client.get_memories(limit=100)
            return json.dumps({
                "memories": [
                    {"id": m.id, "content": m.content, "metadata": m.metadata}
                    for m in memories
                ],
                "count": len(memories)
            }, indent=2)
        
        elif "/summary" in uri_str:
            summary = await client.get_user_summary()
            return json.dumps(summary, indent=2)
        
        else:
            return json.dumps({"error": f"Unknown resource: {uri_str}"})
    
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================
# PROMPTS - Pre-built prompt templates
# ============================================

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="recall_context",
            description="Search memories to get context about the user before responding",
            arguments=[
                PromptArgument(
                    name="topic",
                    description="Topic to search for context about",
                    required=True
                )
            ]
        ),
        Prompt(
            name="save_session",
            description="Save important information from the current conversation",
            arguments=[
                PromptArgument(
                    name="summary",
                    description="Summary of what to remember from this session",
                    required=True
                )
            ]
        )
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    """Get a specific prompt."""
    if name == "recall_context":
        topic = arguments.get("topic", "") if arguments else ""
        return GetPromptResult(
            description=f"Search memories about: {topic}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Before responding, search my memories for any relevant information about: {topic}"
                    )
                )
            ]
        )
    
    elif name == "save_session":
        summary = arguments.get("summary", "") if arguments else ""
        return GetPromptResult(
            description="Save session information",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Please save the following information to my memories: {summary}"
                    )
                )
            ]
        )
    
    raise ValueError(f"Unknown prompt: {name}")


# ============================================
# MAIN ENTRY POINT
# ============================================

async def run_server():
    """Run the MCP server."""
    logger.info("Starting Memphora MCP Server...")
    
    # Validate configuration
    api_key = os.getenv("MEMPHORA_API_KEY")
    if not api_key:
        logger.error("MEMPHORA_API_KEY environment variable not set!")
        logger.error("Please set your Memphora API key:")
        logger.error("  export MEMPHORA_API_KEY='your_api_key_here'")
        sys.exit(1)
    
    # Test connection
    try:
        client = get_client()
        healthy = await client.health_check()
        if healthy:
            logger.info("✓ Connected to Memphora API")
        else:
            logger.warning("⚠ Memphora API health check failed, but continuing...")
    except Exception as e:
        logger.warning(f"⚠ Could not verify Memphora connection: {e}")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server ready - waiting for connections...")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Main entry point."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
