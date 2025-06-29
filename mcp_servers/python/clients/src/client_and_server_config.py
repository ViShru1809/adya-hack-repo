ClientsConfig = [
    "MCP_CLIENT_AZURE_AI",
    "MCP_CLIENT_OPENAI",
    "MCP_CLIENT_GEMINI"
]

ServersConfig = [
    {
        "server_name": "MCP-GSUITE",
        "command": "uv",
        "args": [
            "--directory",
            "../servers/MCP-GSUITE/mcp-gsuite",
            "run",
            "mcp-gsuite"
        ]
    },
    {
        "server_name": "mcp-mermaid",
        "command": "cmd",
        "args": [
            "/c",
            "npx",
            "-y",
            "mcp-mermaid"
        ]
    },
    {
        "server_name": "blender-mcp",
        "command": "cmd",
        "args": [
            "/c",
            "uvx",
            "blender-mcp"
        ]        
    },

    {
        "server_name":"coinstats-mcp",
        "command": "npx",
        "args": [
            "-y",
            "@coinstats/coinstats-mcp"
            ],
            "env": {
                "COINSTATS_API_KEY": "FNdJng7R6gp7l2I4gJa/RX3LjfszShG1fvP9BmcLgWs="
      }
    },

    {
        "server_name" : "readwise-mcp",
        "command": "npx",
        "args": [
            "-y",
            "@readwise/readwise-mcp"
            ],
            "env": {
                "ACCESS_TOKEN": "wSuAgpIPD1lA5Bu0rDgO7VytpDFD6XXYRzLOabn1CSfmtW1Owq"
      }
    }
]