# Concert Planner

> Create a concert planner agent using the Ticketmaster MCP to search for concerts and venue information.

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
          input="""I want to see Taylor Swift perform in New York City. 
          Can you help me find upcoming concerts, get details about the venue, 
          and provide information about ticket prices? I'm particularly interested 
          in accessibility information and seating options.""",
          model="openai/gpt-4.1",
          mcp_servers=["windsor/ticketmaster-mcp"]
      )

      print(f"Concert Planning Results:\n{result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This example uses the Ticketmaster MCP (`windsor/ticketmaster-mcp`).

  Try it out in your projects!
</Tip>
