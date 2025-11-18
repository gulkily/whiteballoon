# Travel Agent

> Creating a travel planning agent that can search for flights, hotels, and provide travel recommendations.

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
          input="""I'm planning a trip to Paris, France from New York City 
          for 5 days in October. Can you help me find:
          1. Flight options and prices
          2. Hotel recommendations in central Paris
          3. Weather forecast for my travel dates
          4. Popular attractions and restaurants
          5. Currency exchange rates and travel tips
          
          My budget is around $3000 total and I prefer mid-range accommodations.""",
          model="openai/gpt-4.1",
          mcp_servers=[
              "joerup/exa-mcp",        # For semantic travel research
              "windsor/brave-search-mcp", # For travel information search
              "joerup/open-meteo-mcp"   # For weather at destination
          ]
      )

      print(f"Travel Planning Results:\n{result.final_output}")

  if __name__ == "__main__":
      asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  Coming soon.
  ```
</CodeGroup>

<Tip>
  This travel agent example uses multiple MCP servers:

  * **Exa MCP** (`joerup/exa-mcp`): For semantic search of travel content and recommendations
  * **Brave Search MCP** (`windsor/brave-search-mcp`): For finding current travel information, reviews, and booking options
  * **Open Meteo MCP** (`joerup/open-meteo-mcp`): For weather forecasts at your destination

  Try these servers out in your projects!
</Tip>
