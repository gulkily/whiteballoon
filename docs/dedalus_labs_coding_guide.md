# Dedalus Labs Integration Guide (Cheat Sheet)

## Core Patterns
- Install the SDK inside `.venv`: `pip install dedalus-labs` (part of `./wb setup`).
- Load API key via `.env` (`DEDALUS_API_KEY`) or pass `api_key` to `AsyncDedalus`.
- Runner workflow:
  ```python
  client = AsyncDedalus()
  runner = DedalusRunner(client)
  result = await runner.run(
      input="...",
      model="openai/gpt-5-mini",
      tools=[...],
      mcp_servers=[...],
      response_format=...
  )
  print(result.final_output)
  ```

## Tool Execution & MCP Servers
- Register callables (`def add(a: int, b: int) -> int`) with docstrings; Runner auto-builds schemas.
- Prefer GPT‑4.1/GPT‑5 for tool-calling reliability.
- `mcp_servers` accepts string or list. Examples from docs:
  ```python
  runner.run(
      input="Plan NYC→Paris trip",
      model="openai/gpt-4.1",
      mcp_servers=[
          "joerup/exa-mcp",      # semantic travel research
          "windsor/brave-search-mcp", # general search
          "joerup/open-meteo-mcp"    # weather
      ]
  )
  ```
- Many providers supported (OpenAI, Anthropic, Google, xAI, DeepSeek, etc.). Set provider-specific env vars (`OPENAI_API_KEY`, etc.).

## Streaming & Structured Outputs
- `runner.run(..., stream=True)` + `stream_async(result)` for live output.
- Client `.stream()` / `.create(stream=True)` also supported; helpers auto-detect event vs chunk streams.
- Structured outputs:
  - `response_format=MyPydanticModel` (Runner or `.parse()`/`.stream()`).
  - Dict schema via `response_format={"type": "json_schema", ...}` for `.create()`.

## Input Styles
- Standard Chat: `messages=[{"role": "user", "content": "..."}]`.
- Dedalus extension: `input="...", instructions="..."` overrides system message.

## Verification Snippet
```python
async def verify(api_key: str) -> tuple[bool, str]:
    client = AsyncDedalus(api_key=api_key)
    runner = DedalusRunner(client)
    try:
        resp = await runner.run(
            input="WhiteBalloon connectivity check",
            model="openai/gpt-5-mini",
        )
    except Exception as exc:
        return False, str(exc)
    return True, resp.final_output or "Verified"
```

## MCP Server Guidelines (from Dedalus docs)
- TypeScript servers: `src/index.ts`, `server.ts`, `tools/`, HTTP transport by default, CLI flag for STDIO in dev. Template: `windsor/brave-search-mcp`.
- Python servers: `src/main.py` using `openmcp` framework (install from Dedalus repo). Template: `dedalus-labs/framework-mcp`.
- Streamable HTTP transport required; servers should be stateless (auth WIP).
- Directory structure includes config, CLI, server, client, type definitions, tools, transport modules.

## Example Use Cases (for reference)
- Travel planner querying multiple MCP servers (Exa + Brave + Open Meteo).
- Web search agent combining semantic search and privacy search MCPs.
- Weather forecaster hitting `joerup/open-meteo-mcp`.
- Concert planner using `windsor/ticketmaster-mcp`.
- These patterns demonstrate mixing LLM reasoning with remote MCP toolkits—good models for WhiteBalloon’s mutual-aid workflows.

## WhiteBalloon Practices
- Store Dedalus API key/timestamp in `.env`; manage via `/admin/dedalus` UI.
- Use `friendly_time` + tooltip (raw ISO) for timestamp displays; apply to any future status indicators.
- Log every Dedalus invocation with success/failure + duration; add daily summary alerts if error rate >5%.
- Context packaging must only include data explicitly marked shareable; enforce via tests.
- Feature-flag the Mutual Aid Copilot per instance (`MUTUAL_AID_COPILOT_ENABLED`) for controlled rollout.
