# Hello World

> Basic chat completion with Dedalus

This example demonstrates the most basic usage of the Dedalus SDK - making a simple chat completion call.

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

      response = await runner.run(
          input="What was the score of the 2025 Wimbledon final?",
          model="openai/gpt-5-mini",
          mcp_servers=["windsor/exa-search-mcp"]
      )

      print(response.final_output)

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>
