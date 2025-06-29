# CoinStats MCP Technical Details

This document provides technical details about the CoinStats MCP server implementation for developers.

## Architecture

The CoinStats MCP server is built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) framework, which allows AI models like Claude to access external APIs and services.

The server is structured as follows:

1. **Entry Point** (`src/index.ts`): Sets up the MCP server and registers all tools
2. **Tool Factory** (`src/tools/toolFactory.ts`): Provides functions to register tools with the MCP server
3. **Tool Configs** (`src/tools/toolConfigs.ts`): Defines all available CoinStats API tools and their parameters
4. **API Requests** (`src/services/request.ts`): Handles the actual API requests to the CoinStats API
5. **Constants** (`src/config/constants.ts`): Stores configuration constants like the API base URL

## Tool Registration Process

Tools are registered with the MCP server via the `registerTools` function:

```typescript
export function registerTools(server: McpServer, toolConfigs: ToolConfig<any>[]) {
    toolConfigs.forEach((config) => {
        server.tool(config.name, config.description, config.parameters, async (params: Record<string, any>) => {
            const basePath = config.basePath || COINSTATS_API_BASE;
            const method = config.method || 'GET';

            // Methods that typically have a request body
            const bodyMethods = ['POST', 'PUT', 'PATCH'];

            // For GET/DELETE requests, all params go in the URL
            // For POST/PUT/PATCH, send params as the body
            if (bodyMethods.includes(method.toUpperCase())) {
                return universalApiHandler(basePath, config.endpoint, method, {}, params);
            } else {
                return universalApiHandler(basePath, config.endpoint, method, params);
            }
        });
    });
}
```

## API Request Handling

API requests are processed through the `universalApiHandler` function:

```typescript
export async function universalApiHandler<T>(
    basePath: string,
    endpoint: string,
    method: string = 'GET',
    params: Record<string, any> = {},
    body?: any
): Promise<{
    content: Array<{ type: 'text'; text: string; isError?: boolean }>;
}> {
    try {
        const url = `${basePath}${endpoint}`;
        const data = await makeRequestCsApi<T>(url, method, params, body);

        if (!data) {
            return {
                content: [{ type: 'text', text: 'Something went wrong', isError: true }],
            };
        }

        return {
            content: [
                {
                    type: 'text',
                    text: JSON.stringify(data),
                },
            ],
        };
    } catch (error) {
        return {
            content: [{ type: 'text', text: `Error: ${error}`, isError: true }],
        };
    }
}
```

## Authentication

The CoinStats API requires an API key, which is passed in the request headers:

```typescript
const headers = {
    'X-API-KEY': COINSTATS_API_KEY,
    'Content-Type': 'application/json',
};
```

The API key is expected to be set as the `COINSTATS_API_KEY` environment variable.

## Adding New Tools

To add a new tool that calls a different CoinStats API endpoint:

1. Add a new configuration to `src/tools/toolConfigs.ts`:

```typescript
export const myNewTool = createToolConfig(
    'mcp_coinstats_mcp_new_function',
    'Description of the new function',
    '/api/endpoint/path',
    {
        param1: z.string().describe('Parameter description'),
        param2: z.number().optional().describe('Optional parameter description')
    },
    'GET' // or 'POST', etc.
);
```

2. Add your new tool to the `allToolConfigs` array in the same file.

## Error Handling

API errors are caught and returned as error objects in the response:

```typescript
return {
    content: [{ type: 'text', text: `Error: ${error}`, isError: true }],
};
```

## Testing

You can test the tools using the Claude Desktop application or by integrating with the [Anthropic API](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/overview) and passing the tool definitions in your requests.
