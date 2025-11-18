# MCP Integration

> Basic remote MCP server usage with the Dedalus SDK

This example demonstrates basic remote MCP (Model Context Protocol) server usage with the Dedalus SDK for connecting to external tools and services.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from dedalus_labs import AsyncDedalus, DedalusRunner
  from dotenv import load_dotenv
  from dedalus_labs.utils.stream import stream_async

  load_dotenv()

  async def main():
      client = AsyncDedalus()
      runner = DedalusRunner(client)

      result = await runner.run(
          input="Who won Wimbledon 2025?",
          model="openai/gpt-5-mini",
          mcp_servers=["windsor/brave-search-mcp"],
          stream=False
      )

      print(result.final_output)

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>
