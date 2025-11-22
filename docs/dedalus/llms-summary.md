# Dedalus Documentation Summary

## Access & Onboarding
- **Use the llms.txt file** (`docs.dedalus/downloads/docs.dedaluslabs.ai-ai-optimizations-llms-txt.md`): Encourage assistants to preload https://docs.dedaluslabs.ai/llms.txt (or llms-full) so they instantly know every endpoint, example, and troubleshooting topic.
- **Quickstart** (`docs.dedalus/downloads/docs.dedaluslabs.ai-index.md`): Walks newcomers through getting an API key, installing the Python/TypeScript SDKs, running Hello World, and trying tool execution. Highlights follow-on examples (streaming, MCP, handoffs, tool chaining) plus community links.
- **Introduction** (`docs.dedalus/downloads/docs.dedaluslabs.ai-introduction.md`): Positions Dedalus as a single drop-in MCP gateway that hosts servers, unifies model access, and accelerates agent delivery.

## Core SDK Patterns
- **Hello World** (`...01-hello-world.md`): Minimal `DedalusRunner` invocation showing chat completions with an MCP server.
- **Basic Tools** (`...02-basic-tools.md`): Runner can expose Python functions as tools; GPT-5/4.1 recommended for reliable tool calling.
- **Streaming** (`...03-streaming.md`): Demonstrates async and sync streaming via `stream=True` and helper utilities `stream_async` / `stream_sync`.
- **MCP Integration** (`...04-mcp-integration.md`): Shows how to attach remote MCP servers (Brave Search) when executing a run.
- **Structured Outputs** (`...05-structured-outputs.md`): Deep dive on Pydantic parsing, streaming, `response_format`, tool + schema enforcement, nested models, refusal handling, provider support matrix, helper utilities, and translation guidance from OpenAI’s Responses API.

## Advanced Workflows
- **Model Handoffs** (`...06-handoffs.md`): Runner accepts a list of models and will route tasks (e.g., GPT for research, Claude for creative writing) while combining MCP search.
- **Tool Chaining** (`...07-tool-chaining.md`): Multi-step workflows mixing custom tools with MCP servers to convert units, recommend clothing, and verify weather.
- **Image Generation & Vision** (`...08-images.md`): Covers `images.generate/edit/create_variation`, base64 and URL-based vision analysis, and orchestrating image pipelines with Runner + helper class.

## Use-Case Playbooks
- **Concert Planner** (`...concert-planner.md`): Uses Ticketmaster MCP to locate shows, venues, and ticket details with accessibility focus.
- **Data Analyst** (`...data-analyst.md`): Combines Brave Search MCP with a Python execution tool to gather financial data and calculate insights.
- **Travel Agent** (`...travel-agent.md`): Chains Exa search, Brave search, and Open Meteo MCP for flights, hotels, weather, and tips under a budget.
- **Weather Forecaster** (`...weather-forecaster.md`): Dedicated Open Meteo MCP workflow for forecasts, precipitation, wind, and planning advice.
- **Web Search Agent** (`...web-search-agent.md`): Multi-search MCP stack to research AI-agent trends, papers, startups, repos, and summarize findings.

## Reference & Operations
- **FAQ** (`docs.dedalus/downloads/docs.dedaluslabs.ai-faq.md`): Reasons to use Dedalus, API key guidance (including BYO keys), language/tooling support, authentication roadmap, and contact channels.
- **Model Providers** (`docs.dedalus/downloads/docs.dedaluslabs.ai-providers.md`): Lists required API keys per provider plus exhaustive supported model catalog across OpenAI, Anthropic, Google, xAI, DeepSeek, etc.
- **MCP Server Guidelines** (`docs.dedalus/downloads/docs.dedaluslabs.ai-server-guidelines.md`): Full architecture blueprint for TypeScript/Python MCP servers including directory layout, config, CLI, strict schemas, HTTP transport, package metadata, and migration checklist.

## Marketing Site Snapshot
- **dedaluslabs.ai** (`docs.dedalus/downloads/dedaluslabs.ai`): Highlights the $11M seed raise, “5 lines of code” positioning, and marketplace story—deploy hosted MCP servers from GitHub, swap between any LLM, mix local tools with hosted MCP endpoints, and upcoming monetization for server creators.

