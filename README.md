# Memphora MCP Server

Add persistent memory to Claude, Cursor, Windsurf, and other AI assistants using the Model Context Protocol (MCP).

## What is this?

This MCP server connects your AI assistant to [Memphora](https://memphora.ai), giving it the ability to:

- **Remember** information across conversations
- **Search** your personal knowledge base
- **Extract** insights from conversations automatically
- **Recall** your preferences, facts, and context

## Quick Start

### 1. Install

```bash
# Using pip
pip install memphora-mcp

# Or using uvx (recommended for Claude Desktop)
uvx memphora-mcp
```

### 2. Get Your API Key

1. Go to [memphora.ai/dashboard](https://memphora.ai/dashboard)
2. Create an account or sign in
3. Copy your API key from the dashboard

### 3. Configure Claude Desktop

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "memphora": {
      "command": "uvx",
      "args": ["memphora-mcp"],
      "env": {
        "MEMPHORA_API_KEY": "your_api_key_here",
        "MEMPHORA_USER_ID": "your_unique_user_id"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Close and reopen Claude Desktop. You should see the Memphora tools available!

## Usage Examples

### Storing Memories

Just tell Claude something about yourself:

```
You: "I work at Google as a software engineer"
Claude: [stores memory] "Got it! I'll remember that you work at Google as a software engineer."

You: "My favorite programming language is Python"
Claude: [stores memory] "Noted! I'll remember that Python is your favorite programming language."
```

### Recalling Memories

Ask Claude about things you've told it before:

```
You: "Where do I work?"
Claude: [searches memories] "You work at Google as a software engineer."

You: "What programming languages do I like?"
Claude: [searches memories] "Your favorite programming language is Python."
```

### Automatic Context

Claude will automatically search your memories when relevant:

```
You: "Can you help me with some code?"
Claude: [searches memories for context]
        "Sure! Since you prefer Python and work at Google, I'll write this in Python 
         following Google's style guide..."
```

## Available Tools

| Tool | Description |
|------|-------------|
| `memphora_search` | Search memories for relevant information |
| `memphora_store` | Store new information for future recall |
| `memphora_extract_conversation` | Extract memories from a conversation |
| `memphora_list_memories` | List all stored memories |
| `memphora_delete` | Delete a specific memory |

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MEMPHORA_API_KEY` | Your Memphora API key | Required |
| `MEMPHORA_USER_ID` | Unique identifier for your memories | `mcp_default_user` |
| `MEMPHORA_API_URL` | API endpoint (optional override) | `https://api.memphora.ai/api/v1` |

## Using with Other MCP Clients

### Cursor

Add to your Cursor settings:

```json
{
  "mcp": {
    "servers": {
      "memphora": {
        "command": "uvx",
        "args": ["memphora-mcp"],
        "env": {
          "MEMPHORA_API_KEY": "your_api_key_here"
        }
      }
    }
  }
}
```

### Windsurf

Add to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "memphora": {
      "command": "python",
      "args": ["-m", "memphora_mcp"],
      "env": {
        "MEMPHORA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Development

### Running Locally

```bash
# Clone the repo
git clone https://github.com/Memphora/memphora-mcp.git
cd memphora-mcp

# Install dependencies
pip install -e ".[dev]"

# Set your API key
export MEMPHORA_API_KEY="your_key"

# Run the server
python -m memphora_mcp
```

### Testing

```bash
pytest tests/
```

## Privacy & Security

- Your memories are stored securely in Memphora's cloud
- Each user has isolated memory storage
- API keys are stored locally on your machine
- All communication is encrypted via HTTPS

## Support

- Documentation: [docs.memphora.ai](https://docs.memphora.ai)
- Issues: [GitHub Issues](https://github.com/Memphora/memphora-mcp/issues)
- Email: support@memphora.ai

## License

MIT License - see [LICENSE](LICENSE) for details.
