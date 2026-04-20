# MCP Servers Collection

A collection of [Model Context Protocol (MCP)](https://modelcontextprotocol.io) servers for integrating AI assistants with various APIs and services.

## Available MCP Servers

| MCP Server | Description | Status |
|------------|-------------|--------|
| [freshdesk-mcp](./freshdesk-mcp/) | Full Freshdesk API integration - tickets, contacts, companies, agents, knowledge base | ✅ Ready |

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). Think of MCP like a USB-C port for AI applications — it provides a standardized way to connect AI models to different data sources and tools.

## Repository Structure

```
mcp/
├── README.md                 # This file - overview of all MCP servers
├── .gitignore               # Global gitignore for the repository
├── freshdesk-mcp/           # Freshdesk MCP server
│   ├── README.md            # Detailed documentation
│   ├── server.py            # MCP server implementation
│   ├── requirements.txt     # Python dependencies
│   ├── env.example          # Environment variables template
│   └── claude_desktop_config.json  # Claude Desktop configuration example
└── [future-mcp-server]/     # Template for new MCP servers
```

## Quick Start

Each MCP server has its own README with detailed setup instructions. Generally:

1. Navigate to the MCP server directory
2. Install dependencies (`pip install -r requirements.txt`)
3. Copy `env.example` to `.env` and fill in your credentials
4. Configure your MCP client (Claude Desktop, etc.)
5. Start using the tools!

## Adding a New MCP Server

To add a new MCP server to this repository:

1. Create a new directory: `your-service-mcp/`
2. Include the following files:
   - `README.md` - Detailed documentation with setup instructions
   - `server.py` - MCP server implementation
   - `requirements.txt` - Python dependencies
   - `env.example` - Template for environment variables (no real credentials)
   - `.gitignore` - Service-specific ignores
   - `claude_desktop_config.json` - Example configuration

3. Update this root README.md to include the new MCP in the table
4. Ensure all documentation is in English

## Contributing

When contributing new MCP servers or improvements:

- Keep credentials out of the repository (use `env.example` with placeholder values)
- Write clear documentation in English
- Test with Claude Desktop or other MCP clients
- Follow the existing directory structure and naming conventions

## License

MIT License - See individual MCP server directories for specific licensing information.

