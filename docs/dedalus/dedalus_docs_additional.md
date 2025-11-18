# Model Providers

> Mix and match models from supported providers.

<CardGroup cols={3}>
  <Card title="OpenAI" icon="robot">
    `OPENAI_API_KEY`
  </Card>

  <Card title="Anthropic" icon="brain">
    `ANTHROPIC_API_KEY`
  </Card>

  <Card title="Google Gemini" icon="google">
    `GOOGLE_API_KEY`
  </Card>

  <Card title="Fireworks AI" icon="fire">
    `FIREWORKS_API_KEY`
  </Card>

  <Card title="xAI" icon="x">
    `XAI_API_KEY`
  </Card>

  <Card title="Perplexity" icon="circle-question">
    `PERPLEXITY_API_KEY`
  </Card>

  <Card title="DeepSeek" icon="magnifying-glass">
    `DEEPSEEK_API_KEY`
  </Card>

  <Card title="Groq" icon="bolt">
    `GROQ_API_KEY`
  </Card>

  <Card title="Cohere" icon="comments">
    `COHERE_API_KEY`
  </Card>

  <Card title="Together AI" icon="users">
    `TOGETHERAPI_KEY`
  </Card>

  <Card title="Cerebras" icon="microchip">
    `CEREBRAS_API_KEY`
  </Card>

  <Card title="Mistral" icon="wind">
    `MISTRAL_API_KEY`
  </Card>
</CardGroup>

## Supported Models

### OpenAI

#### Chat Models

* `openai/gpt-5`
* `openai/gpt-5-mini`
* `openai/gpt-5-nano`
* `openai/gpt-5-chat-latest`
* `openai/gpt-5-codex`
* `openai/gpt-5-pro`
* `openai/gpt-4.1`
* `openai/gpt-4.1-mini`
* `openai/gpt-4.1-nano`
* `openai/gpt-4o`
* `openai/gpt-4o-2024-05-13`
* `openai/gpt-4o-mini`
* `openai/gpt-4o-search-preview`
* `openai/gpt-4o-mini-search-preview`
* `openai/chatgpt-4o-latest`
* `openai/gpt-4-turbo`
* `openai/gpt-4-turbo-2024-04-09`
* `openai/gpt-4`
* `openai/gpt-4-0125-preview`
* `openai/gpt-4-1106-preview`
* `openai/gpt-4-1106-vision-preview`
* `openai/gpt-4-0613`
* `openai/gpt-4-0314`
* `openai/gpt-4-32k`
* `openai/gpt-3.5-turbo`
* `openai/gpt-3.5-turbo-0125`
* `openai/gpt-3.5-turbo-1106`
* `openai/gpt-3.5-turbo-0613`
* `openai/gpt-3.5-0301`
* `openai/gpt-3.5-turbo-instruct`
* `openai/gpt-3.5-turbo-16k-0613`

#### Reasoning Models

* `openai/o1`
* `openai/o1-pro`
* `openai/o1-mini`
* `openai/o1-preview`
* `openai/o3`
* `openai/o3-pro`
* `openai/o3-mini`
* `openai/o3-deep-research`
* `openai/o4-mini`
* `openai/o4-mini-deep-research`

#### Image Generation

* `openai/dall-e-3`

#### Audio Transcription

* `openai/whisper-1`

### Anthropic (Claude)

#### Claude 4.5 Series

* `anthropic/claude-haiku-4-5-20251001`
* `anthropic/claude-sonnet-4-5-20250929`

#### Claude 4 Series

* `anthropic/claude-opus-4-1-20250805`
* `anthropic/claude-opus-4-20250514`
* `anthropic/claude-sonnet-4-20250514`

#### Claude 3.7 Series

* `anthropic/claude-3-7-sonnet-20250219`

#### Claude 3.5 Series

* `anthropic/claude-3-5-sonnet-20241022`
* `anthropic/claude-3-5-haiku-20241022`

#### Claude 3 Series

* `anthropic/claude-3-opus-20240229`
* `anthropic/claude-3-sonnet-20240229`
* `anthropic/claude-3-haiku-20240307`

### Google (Gemini)

#### Gemini 2.5 Series

* `google/gemini-2.5-pro`
* `google/gemini-2.5-flash`
* `google/gemini-2.5-flash-lite`

#### Gemini 2.0 Series

* `google/gemini-2.0-flash`
* `google/gemini-2.0-flash-exp`
* `google/gemini-2.0-flash-001`
* `google/gemini-2.0-flash-lite`

#### Gemini 1.5 Series

* `google/gemini-1.5-pro`
* `google/gemini-1.5-flash`

### xAI (Grok)

#### Grok 4 Series

* `xai/grok-4-fast-reasoning`
* `xai/grok-4-fast-non-reasoning`
* `xai/grok-code-fast-1`
* `xai/grok-4-0709`

#### Grok 3 Series

* `xai/grok-3`
* `xai/grok-3-mini`

#### Grok 2 Series

* `xai/grok-2`
* `xai/grok-2-1212`
* `xai/grok-2-vision-1212`

#### Legacy

* `xai/grok-beta`

### DeepSeek

* `deepseek/deepseek-chat`
* `deepseek/deepseek-reasoner`
* `deepseek/deepseek-coder`


# MCP Server Guidelines

> Ensure your server works with the Dedalus platform.

<Warning>
  We're open-sourcing an MCP framework to help users easily build and deploy their MCP servers in October 2025.
  Until then, users are encouraged to structure their MCP servers according to the [templates](#key-details) below.
</Warning>

# Key Details

* **We support both TypeScript and Python servers:**
  * **TypeScript servers:** We look for an `index.ts` in `src/`. The simplest server is a repo with a `src/` folder with `index.ts` in it that starts the server. Use this [template](https://github.com/windsornguyen/brave-search-mcp) ([copy as markdown](https://gitingest.com/dedalus-labs/brave-search-mcp)).
  * **Python servers:** We look for a `main.py` in `src/`. The simplest server is a repo with a `src/` folder with `main.py` in it that starts the server. Use this [template](https://github.com/dedalus-labs/framework-mcp) ([copy as markdown](https://gitingest.com/dedalus-labs/framework-mcp)). Dedalus has open-sourced the MCP framework—install the required `openmcp` package with:

    ```
    git clone https://github.com/dedalus-labs/openmcp-python

    cd openmcp-python    # Keep here so Claude/Codex can inspect

    uv pip install -e .  # Install as an editable

    uv pip show openmcp  # Should display a version

    #Don't forget to active your virtual environment
    ```
* Since servers will be remotely deployed, they must use the streamable HTTP transport method.

<Warning>
  Authentication is under rapid development but is not currently supported. Accordingly, your servers should be stateless and not require auth.
</Warning>

# Full MCP Server Architecture Guide

<Tip>
  Pro tip: Click the "Copy page" button to paste this page as context to your coding assistant to refactor your existing server to follow our recommended specification.
</Tip>

## Overview

This guide defines the standard architecture and conventions for Model Context Protocol (MCP) servers with streamable HTTP transport. This structure ensures consistency, maintainability, and production readiness across all MCP server implementations.

## Core Principles

1. **Modular Architecture** - Clear separation of concerns with dedicated modules
2. **Streamable HTTP First** - Modern HTTP transport as the primary interface
3. **Type Safety** - Full TypeScript coverage with proper interfaces
4. **Production Ready** - Built-in error handling, logging, and configuration management
5. **Testable** - Dependency injection and isolated components

## Directory Structure

```
project-root/
├── src/
│   ├── index.ts            # Main entry point
│   ├── cli.ts              # Command-line argument parsing
│   ├── config.ts           # Configuration management
│   ├── server.ts           # Server instance creation
│   ├── client.ts           # External API client
│   ├── types.ts            # TypeScript type definitions
│   ├── tools/
│   │   ├── index.ts        # Tool exports
│   │   └── [service].ts    # Tool definitions and handlers
│   └── transport/
│       ├── index.ts        # Transport exports
│       ├── http.ts         # HTTP transport (primary)
│       └── stdio.ts        # STDIO transport (development)
├── package.json
├── tsconfig.json
└── .gitignore
```

## Implementation Guide

### 1. Main Entry Point (`src/index.ts`)

The main entry point should handle transport selection and error management:

```typescript  theme={null}
#!/usr/bin/env node

import { config as loadEnv } from 'dotenv';
loadEnv();

import { loadConfig } from './config.js';
import { parseArgs } from './cli.js';
import { [Service]Server } from './server.js';
import { runStdioTransport, startHttpTransport } from './transport/index.js';

/**
 * Transport selection logic:
 * 1. --stdio flag forces STDIO transport
 * 2. Default: HTTP transport for production compatibility
 */
async function main() {
    try {
        const config = loadConfig();
        const cliOptions = parseArgs();
        
        if (cliOptions.stdio) {
            // STDIO transport for local development
            const server = new [Service]Server(config.apiKey);
            await runStdioTransport(server.getServer());
        } else {
            // HTTP transport for production/cloud deployment
            const port = cliOptions.port || config.port;
            startHttpTransport({ ...config, port });
        }
    } catch (error) {
        console.error("Fatal error running [Service] server:", error);
        process.exit(1);
    }
}

main();
```

### 2. Configuration Management (`src/config.ts`)

Centralized configuration with environment variable validation:

```typescript  theme={null}
import dotenv from 'dotenv';
dotenv.config();

export interface Config {
    apiKey: string;
    port: number;
    isProduction: boolean;
}

export function loadConfig(): Config {
    const apiKey = process.env['[SERVICE]_API_KEY'];
    if (!apiKey) {
        throw new Error('[SERVICE]_API_KEY environment variable is required');
    }

    const port = parseInt(process.env.PORT || '8080', 10);
    const isProduction = process.env.NODE_ENV === 'production';

    return { apiKey, port, isProduction };
}
```

### 3. Command Line Interface (`src/cli.ts`)

Standardized CLI with help documentation:

```typescript  theme={null}
export interface CliOptions {
    port?: number;
    stdio?: boolean;
}

export function parseArgs(): CliOptions {
    const args = process.argv.slice(2);
    const options: CliOptions = {};
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--port':
                if (i + 1 < args.length) {
                    options.port = parseInt(args[i + 1], 10);
                    i++;
                } else {
                    throw new Error('--port flag requires a value');
                }
                break;
            case '--stdio':
                options.stdio = true;
                break;
            case '--help':
                printHelp();
                process.exit(0);
                break;
        }
    }
    return options;
}

function printHelp(): void {
    console.log(`
[Service] MCP Server

USAGE:
    [service] [OPTIONS]

OPTIONS:
    --port <PORT>    Run HTTP server on specified port (default: 8080)
    --stdio          Use STDIO transport instead of HTTP
    --help           Print this help message

ENVIRONMENT VARIABLES:
    [SERVICE]_API_KEY    Required: Your [Service] API key
    PORT                 HTTP server port (default: 8080)
    NODE_ENV            Set to 'production' for production mode
`);
}
```

### 4. Type Definitions (`src/types.ts`)

All TypeScript interfaces and types:

```typescript  theme={null}
/**
 * Arguments for [tool_name] tool
 */
export interface [Tool]Args {
    // Define tool-specific arguments
    query: string;
    options?: Record<string, unknown>;
}

/**
 * External API response structure
 */
export interface [Service]Response {
    // Define API response structure
    data: unknown;
    metadata?: Record<string, unknown>;
}
```

### 5. External API Client (`src/client.ts`)

Dedicated client for external API interactions:

```typescript  theme={null}
import { [Service]Response } from './types.js';

export class [Service]Client {
    private apiKey: string;
    private baseUrl: string = 'https://api.[service].com';

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    /**
     * Performs API request with proper error handling
     */
    async performRequest(params: unknown): Promise<string> {
        const response = await fetch(`${this.baseUrl}/endpoint`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`,
            },
            body: JSON.stringify(params),
        });

        if (!response.ok) {
            let errorText: string;
            try {
                errorText = await response.text();
            } catch {
                errorText = "Unable to parse error response";
            }
            throw new Error(
                `[Service] API error: ${response.status} ${response.statusText}\n${errorText}`
            );
        }

        const data: [Service]Response = await response.json();
        return this.formatResponse(data);
    }

    private formatResponse(data: [Service]Response): string {
        // Format response according to service requirements
        return JSON.stringify(data, null, 2);
    }
}
```

### 6. Tool Definitions (`src/tools/[service].ts`)

Tool definitions with handlers following the established pattern:

```typescript  theme={null}
import { Tool, CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { [Service]Client } from '../client.js';
import { [Tool]Args } from '../types.js';

/**
 * Tool definition for [tool_name]
 */
export const [tool]ToolDefinition: Tool = {
    name: "[service]_[action]",
    description: "Description of what this tool does and when to use it.",
    inputSchema: {
        type: "object",
        properties: {
            // Define input schema
        },
        required: ["required_field"],
    },
};

/**
 * Type guard for [tool] arguments
 */
function is[Tool]Args(args: unknown): args is [Tool]Args {
    return (
        typeof args === "object" &&
        args !== null &&
        "required_field" in args &&
        typeof (args as { required_field: unknown }).required_field === "string"
    );
}

/**
 * Handles [tool] tool calls
 */
export async function handle[Tool]Tool(
    client: [Service]Client, 
    args: unknown
): Promise<CallToolResult> {
    try {
        if (!args) {
            throw new Error("No arguments provided");
        }

        if (!is[Tool]Args(args)) {
            throw new Error("Invalid arguments for [service]_[action]");
        }

        const result = await client.performRequest(args);
        
        return {
            content: [{ type: "text", text: result }],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: "text",
                    text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
}
```

### 7. Tool Exports (`src/tools/index.ts`)

Centralized tool exports:

```typescript  theme={null}
export {
    [tool]ToolDefinition,
    handle[Tool]Tool,
    // Export all tool definitions and handlers
} from './[service].js';
```

### 8. Server Instance (`src/server.ts`)

Server configuration with tool registration:

```typescript  theme={null}
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    InitializedNotificationSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { [Service]Client } from './client.js';
import {
    [tool]ToolDefinition,
    handle[Tool]Tool,
} from './tools/index.js';

export function createStandaloneServer(apiKey: string): Server {
    const serverInstance = new Server(
        {
            name: "org/[service]",
            version: "0.2.0",
        },
        {
            capabilities: {
                tools: {},
            },
        }
    );

    const [service]Client = new [Service]Client(apiKey);

    serverInstance.setNotificationHandler(InitializedNotificationSchema, async () => {
        console.log('[Service] MCP client initialized');
    });

    serverInstance.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [[tool]ToolDefinition],
    }));

    serverInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        
        switch (name) {
            case "[service]_[action]":
                return await handle[Tool]Tool([service]Client, args);
            default:
                return {
                    content: [{ type: "text", text: `Unknown tool: ${name}` }],
                    isError: true,
                };
        }
    });

    return serverInstance;
}

export class [Service]Server {
    private apiKey: string;

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    getServer(): Server {
        return createStandaloneServer(this.apiKey);
    }
}
```

### 9. HTTP Transport (`src/transport/http.ts`)

Streamable HTTP transport with session management:

```typescript  theme={null}
import { createServer, IncomingMessage, ServerResponse } from 'http';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { randomUUID } from 'crypto';
import { createStandaloneServer } from '../server.js';
import { Config } from '../config.js';

const sessions = new Map<string, { transport: StreamableHTTPServerTransport; server: any }>();

export function startHttpTransport(config: Config): void {
    const httpServer = createServer();

    httpServer.on('request', async (req, res) => {
        const url = new URL(req.url!, `http://${req.headers.host}`);

        switch (url.pathname) {
            case '/mcp':
                await handleMcpRequest(req, res, config);
                break;
            case '/sse':
                await handleSSERequest(req, res, config);
                break;
            case '/health':
                handleHealthCheck(res);
                break;
            default:
                handleNotFound(res);
        }
    });

    const host = config.isProduction ? '0.0.0.0' : 'localhost';
    
    httpServer.listen(config.port, host, () => {
        logServerStart(config);
    });
}

async function handleMcpRequest(
    req: IncomingMessage,
    res: ServerResponse,
    config: Config
): Promise<void> {
    const sessionId = req.headers['mcp-session-id'] as string | undefined;

    if (sessionId) {
        const session = sessions.get(sessionId);
        if (!session) {
            res.statusCode = 404;
            res.end('Session not found');
            return;
        }
        return await session.transport.handleRequest(req, res);
    }

    if (req.method === 'POST') {
        await createNewSession(req, res, config);
        return;
    }

    res.statusCode = 400;
    res.end('Invalid request');
}

async function handleSSERequest(
    req: IncomingMessage,
    res: ServerResponse,
    config: Config
): Promise<void> {
    const serverInstance = createStandaloneServer(config.apiKey);
    const transport = new SSEServerTransport('/sse', res);
    
    try {
        await serverInstance.connect(transport);
        console.log('SSE connection established');
    } catch (error) {
        console.error('SSE connection error:', error);
        res.statusCode = 500;
        res.end('SSE connection failed');
    }
}

async function createNewSession(
    req: IncomingMessage,
    res: ServerResponse,
    config: Config
): Promise<void> {
    const serverInstance = createStandaloneServer(config.apiKey);
    const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: (sessionId) => {
            sessions.set(sessionId, { transport, server: serverInstance });
            console.log('New [Service] session created:', sessionId);
        }
    });

    transport.onclose = () => {
        if (transport.sessionId) {
            sessions.delete(transport.sessionId);
            console.log('[Service] session closed:', transport.sessionId);
        }
    };

    try {
        await serverInstance.connect(transport);
        await transport.handleRequest(req, res);
    } catch (error) {
        console.error('Streamable HTTP connection error:', error);
        res.statusCode = 500;
        res.end('Internal server error');
    }
}

function handleHealthCheck(res: ServerResponse): void {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        service: '[service]-mcp',
        version: '0.2.0'
    }));
}

function handleNotFound(res: ServerResponse): void {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
}

function logServerStart(config: Config): void {
    const displayUrl = config.isProduction 
        ? `Port ${config.port}` 
        : `http://localhost:${config.port}`;
    
    console.log(`[Service] MCP Server listening on ${displayUrl}`);

    if (!config.isProduction) {
        console.log('Put this in your client config:');
        console.log(JSON.stringify({
            "mcpServers": {
                "[service]": {
                    "url": `http://localhost:${config.port}/mcp`
                }
            }
        }, null, 2));
        console.log('For backward compatibility, you can also use the /sse endpoint.');
    }
}
```

### 10. STDIO Transport (`src/transport/stdio.ts`)

Simple STDIO transport for development:

```typescript  theme={null}
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

export async function runStdioTransport(server: Server): Promise<void> {
    const transport = new StdioServerTransport();
    
    try {
        await server.connect(transport);
        console.error("[Service] MCP Server running on stdio");
    } catch (error) {
        console.error("Failed to start STDIO transport:", error);
        throw error;
    }
}
```

### 11. Transport Exports (`src/transport/index.ts`)

```typescript  theme={null}
export { startHttpTransport } from './http.js';
export { runStdioTransport } from './stdio.js';
```

## Configuration Files

### package.json Configuration

```json  theme={null}
{
  "name": "[service]-mcp-server",
  "version": "0.2.0",
  "type": "module",
  "main": "dist/index.js",
  "bin": {
    "[service]-mcp": "dist/index.js"
  },
  "files": [
    "dist"
  ],
  "scripts": {
    "build": "tsc && shx chmod +x dist/*.js",
    "prepare": "npm run build",
    "watch": "tsc --watch",
    "start": "node dist/index.js",
    "start:stdio": "node dist/index.js --stdio",
    "dev": "tsc && node dist/index.js",
    "dev:stdio": "tsc && node dist/index.js --stdio"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.17.3"
  }
}
```

**Key Configuration Points:**

* `"main": "dist/index.js"` - Points to compiled entry point
* `"bin"` - Makes the server executable as a CLI tool
* `"files": ["dist"]` - Only includes compiled code in npm package
* `"type": "module"` - Enables ES modules
* `"@modelcontextprotocol/sdk": "^1.17.3"` - **Required**: Version 1.16.0+ needed for StreamableHTTPServerTransport

### TypeScript Configuration

```json  theme={null}
{
  "compilerOptions": {
    "target": "ES2015",
    "module": "ESNext",
    "outDir": "./dist",
    "rootDir": ".",
    "strict": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "moduleResolution": "node"
  },
  "include": [
    "src/**/*.ts"
  ],
  "exclude": [
    "node_modules",
    "dist"
  ]
}
```

**Build Process:**

1. TypeScript compiles `src/index.ts` → `dist/index.js`
2. Package.json points to compiled version
3. Build script makes output executable
4. No root-level index.ts needed

### .gitignore

```gitignore  theme={null}
# Build artifacts
node_modules/
dist/
npm-debug.log
yarn-error.log

# Environment files
.env
*.env

# IDE files
.vscode/
.idea/
*.swp
*.swo

# System files
.DS_Store
Thumbs.db
```

## Best Practices

### 1. Error Handling

* Always wrap API calls in try-catch blocks
* Provide meaningful error messages
* Log errors for debugging while sanitizing sensitive data

### 2. Type Safety

* Define interfaces for all data structures
* Use type guards for runtime validation
* Enable strict TypeScript checking

### 3. Session Management

* Implement proper session cleanup
* Handle connection timeouts
* Monitor memory usage for session storage

### 4. Production Readiness

* Use environment variables for configuration
* Implement health checks
* Add structured logging
* Consider rate limiting for external APIs

### 5. Testing

* Keep components isolated for easy unit testing
* Mock external API clients in tests
* Test both transport methods

## Migration Checklist

When refactoring an existing MCP server to this architecture:

* [ ] Create modular directory structure with `src/` folder
* [ ] Move main entry point to `src/index.ts` (single entry point)
* [ ] Extract configuration management (`src/config.ts`)
* [ ] Separate CLI argument parsing (`src/cli.ts`)
* [ ] Create dedicated API client class (`src/client.ts`)
* [ ] Define TypeScript interfaces (`src/types.ts`)
* [ ] Create server instance factory (`src/server.ts`)
* [ ] Move tool definitions to separate files (`src/tools/[service].ts`)
* [ ] Implement modular transport system (`src/transport/`)
* [ ] Add streamable HTTP transport as primary
* [ ] Configure package.json to point to `dist/index.js`
* [ ] Set up proper TypeScript compilation (`src/` → `dist/`)
* [ ] Add health check endpoint
* [ ] Update build scripts and .gitignore
* [ ] Add proper error handling throughout
* [ ] Test both HTTP and STDIO transport methods

This architecture ensures consistency, maintainability, and production readiness across all MCP server implementations while prioritizing the modern streamable HTTP transport.


